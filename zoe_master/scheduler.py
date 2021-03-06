# Copyright (c) 2016, Daniele Venzano
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""The Scheduler."""

import logging
import threading

from zoe_lib.sql_manager import Execution

from zoe_master.exceptions import ZoeStartExecutionFatalException, ZoeStartExecutionRetryException
from zoe_master.zapp_to_docker import execution_to_containers, terminate_execution

log = logging.getLogger(__name__)


class ZoeScheduler:
    """The Scheduler class."""
    def __init__(self):
        self.fifo_queue = []
        self.trigger_semaphore = threading.Semaphore(0)
        self.async_threads = []
        self.loop_quit = False
        self.loop_th = threading.Thread(target=self.loop_start_th, name='scheduler')
        self.loop_th.start()

    def trigger(self):
        """Trigger a scheduler run."""
        self.trigger_semaphore.release()

    def incoming(self, execution: Execution):
        """
        This method adds the execution to the end of the FIFO queue and triggers the scheduler.
        :param execution: The execution
        :return:
        """
        self.fifo_queue.append(execution)
        self.trigger()

    def terminate(self, execution: Execution) -> None:
        """
        Inform the master that an execution has been terminated. This can be done asynchronously.
        :param execution: the terminated execution
        :return: None
        """
        def async_termination():
            """Actual termination run in a thread."""
            terminate_execution(execution)
            self.trigger()

        try:
            self.fifo_queue.remove(execution)
        except ValueError:
            pass
        th = threading.Thread(target=async_termination, name='termination_{}'.format(execution.id))
        th.start()
        self.async_threads.append(th)

    def remove_execution(self, execution: Execution):
        """Removes the execution form the queue."""
        try:
            self.fifo_queue.remove(execution)
        except ValueError:
            pass

    def loop_start_th(self):
        """The Scheduler thread loop."""
        while True:
            ret = self.trigger_semaphore.acquire(timeout=1)
            if not ret:  # Semaphore timeout, do some thread cleanup
                counter = len(self.async_threads)
                while counter > 0:
                    if len(self.async_threads) == 0:
                        break
                    th = self.async_threads.pop(0)
                    th.join(0.1)
                    if th.isAlive():  # join failed
                        log.debug('Thread {} join failed'.format(th.name))
                        self.async_threads.append(th)
                    counter -= 1
                continue
            if self.loop_quit:
                break

            log.debug("Scheduler start loop has been triggered")
            if len(self.fifo_queue) == 0:
                continue

            e = self.fifo_queue[0]
            assert isinstance(e, Execution)
            e.set_starting()
            self.fifo_queue.pop(0)  # remove the execution form the queue

            try:
                execution_to_containers(e)
            except ZoeStartExecutionRetryException as ex:
                log.warning('Temporary failure starting execution {}: {}'.format(e.id, ex.message))
                e.set_error_message(ex.message)
                terminate_execution(e)
                e.set_scheduled()
                self.fifo_queue.append(e)
            except ZoeStartExecutionFatalException as ex:
                log.error('Fatal error trying to start execution {}: {}'.format(e.id, ex.message))
                e.set_error_message(ex.message)
                terminate_execution(e)
                e.set_error()
            except Exception as ex:
                log.exception('BUG, this error should have been caught earlier')
                e.set_error_message(str(ex))
                terminate_execution(e)
                e.set_error()
            else:
                e.set_running()

    def quit(self):
        """Stop the scheduler thread."""
        self.loop_quit = True
        self.trigger()
        self.loop_th.join()

    def stats(self):
        """Scheduler statistics."""
        return {
            'queue_length': len(self.fifo_queue),
            'termination_threads_count': len(self.async_threads)
        }

