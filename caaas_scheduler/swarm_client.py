import docker
import docker.utils

from common.configuration import conf

from caaas_scheduler.swarm_status import SwarmStatus


class SwarmClient:
    def __init__(self):
        manager = conf['docker_swarm_manager']
        self.cli = docker.Client(base_url=manager)

    def info(self) -> SwarmStatus:
        info = self.cli.info()
        pl_status = SwarmStatus()
        pl_status.container_count = info["Containers"]
        pl_status.image_count = info["Images"]
        pl_status.memory_total = info["MemTotal"]
        pl_status.cores_total = info["NCPU"]

        # DriverStatus is a list...
        idx = 1
        assert 'Strategy' in info["DriverStatus"][idx][0]
        pl_status.placement_strategy = info["DriverStatus"][idx][1]
        idx = 2
        assert 'Filters' in info["DriverStatus"][idx][0]
        pl_status.active_filters = info["DriverStatus"][idx][1].split(", ")

        return pl_status

    def spawn_container(self, image, options):
        host_config = docker.utils.create_host_config(network_mode="bridge",
                                                      binds=options.get_volume_binds(),
                                                      mem_limit=options.get_memory_limit())
        cont = self.cli.create_container(image=image,
                                         environment=options.get_environment(),
                                         network_disabled=False,
                                         host_config=host_config,
                                         detach=True,
                                         volumes=options.get_volumes(),
                                         command=options.get_command())
        self.cli.start(container=cont.get('Id'))
        return self.inspect_container(cont.get('Id'))

    def inspect_container(self, docker_id):
        docker_info = self.cli.inspect_container(container=docker_id)
        info = {
            "docker_ip": docker_info["NetworkSettings"]["IPAddress"]
        }
        return info

    def terminate_container(self, docker_id):
        self.cli.remove_container(docker_id, force=True)


class ContainerOptions:
    def __init__(self):
        self.env = {}
        self.volume_binds = []
        self.volumes = []
        self.command = ""
        self.memory_limit = '2g'

    def add_env_variable(self, name, value):
        self.env[name] = value

    def get_environment(self):
        return self.env

    def add_volume_bind(self, path, mountpoint, readonly=False):
        self.volumes.append(mountpoint)
        self.volume_binds.append(path + ":" + mountpoint + ":" + "ro" if readonly else "rw")

    def get_volumes(self):
        return self.volumes

    def get_volume_binds(self):
        return self.volume_binds

    def set_command(self, cmd):
        self.command = cmd

    def get_command(self):
        return self.command

    def set_memory_limit(self, limit):
        self.memory_limit = limit

    def get_memory_limit(self):
        return self.memory_limit
