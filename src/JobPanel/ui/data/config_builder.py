# -*- coding: utf-8 -*-
"""
Factory for generating config files.
@author: Jan Gabriel
@contact: jan.gabriel@tul.cz
"""
import copy
import os
import uuid
import json
import gm_base.config as config

import JobPanel.communication.installation as ins
from JobPanel.communication import Installation
from JobPanel.data.communicator_conf import PbsConfig, SshConfig, PythonEnvConfig, \
    LibsEnvConfig, CommunicatorConfig, CommType, OutputCommType, InputCommType, \
    CommunicatorConfigService
from ...ui.dialogs.resource_dialog import UiResourceDialog
from JobPanel.data import Users
from ...ui.dialogs import SshPasswordDialog
from gm_base.geomop_analysis import Analysis, InvalidAnalysis
from ...ui.imports.workspaces_conf import BASE_DIR

from gm_base.version import Version

# TODO: If this code will be used must: remove copy of pyssh.
JOB_NAME_LABEL = "flow"
COPY_EX_LIBS = ['pyssh']
EX_LIB_PATH = os.path.join(os.path.split(
    os.path.dirname(os.path.realpath(__file__)))[0], "..", "..", "gm_base")


class ConfigBuilder:
    def __init__(self, data):
        self.multijobs = data.multijobs
        self.ssh_presets = data.ssh_presets
        self.pbs_presets = data.pbs_presets
        self.resource_presets = data.resource_presets
        self.env_presets = data.env_presets
        self.workspaces = data.workspaces
        self.config = data.config

        self.app_version = Version().version
        """
        Application version. If version in remote installation is different
        new installation is created.
        """

        self.conf_long_id = str(uuid.uuid4())
        """
        Long id of configuration. If  in remote installation is different
        id new configuration is reloaded.
        """

    def build(self, key):
        """
        Build json config files into the ./jobs/mj_name/mj_conf
        :param key: Identification of preset.
        :return: app_conf
        """
        # multijob preset properties
        mj_preset = self.multijobs[key].preset
        mj_name = mj_preset.name
        an_name = mj_preset.analysis
        res_preset = self.resource_presets[mj_preset.resource_preset]
        mj_log_level = mj_preset.log_level
        mj_number_of_processes = mj_preset.number_of_processes
 
        # resource preset
        mj_execution_type = res_preset.mj_execution_type
        mj_ssh_preset = self.ssh_presets.get(res_preset.mj_ssh_preset, None)
        mj_remote_execution_type = res_preset.mj_remote_execution_type
        mj_pbs_preset = self.pbs_presets.get(res_preset.mj_pbs_preset, None)
        if mj_ssh_preset is None:
            mj_env = self.config.local_env
        else:
            mj_env = mj_ssh_preset.env
        mj_env = self.env_presets[mj_env]

        j_execution_type = res_preset.j_execution_type
        j_ssh_preset = self.ssh_presets.get(res_preset.j_ssh_preset, None)
        j_remote_execution_type = res_preset.j_remote_execution_type
        j_pbs_preset = self.pbs_presets.get(res_preset.j_pbs_preset, None)
        if j_ssh_preset is None:
            j_env = mj_env            
        else:
            j_env = j_ssh_preset.env
            j_env = self.env_presets[j_env]

        # init conf
        basic_conf = CommunicatorConfig()
        basic_conf.mj_name = mj_name
        basic_conf.an_name = an_name
        basic_conf.log_level = mj_log_level
        basic_conf.number_of_processes = mj_number_of_processes
        basic_conf.app_version = self.app_version
        basic_conf.conf_long_id = self.conf_long_id

        # make conf
        mj_ssh = ConfFactory.get_ssh_conf(mj_ssh_preset, mj_name, an_name, self.conf_long_id)
        if hasattr(mj_ssh_preset, "pbs_system"):
           mj_dialect = mj_ssh_preset.pbs_system
        else:
            mj_dialect = None
        mj_pbs = ConfFactory.get_pbs_conf(mj_pbs_preset, True, pbs_params=mj_env.pbs_params,
                                          dialect=mj_dialect)
        mj_python_env, mj_libs_env = ConfFactory.get_env_conf(mj_env)

        # env conf
        j_ssh = ConfFactory.get_ssh_conf(j_ssh_preset, mj_name, an_name, self.conf_long_id, True)
        if hasattr(j_ssh_preset, "pbs_system"):
            j_dialect = j_ssh_preset.pbs_system
        elif hasattr(mj_ssh_preset, "pbs_system"):
            # for PBS -> PBS dialect from mj ssh preset
            j_dialect = mj_ssh_preset.pbs_system
        else:
            j_dialect = None        
        if (res_preset.mj_execution_type == UiResourceDialog.EXEC_LABEL and
                res_preset.j_execution_type == UiResourceDialog.PBS_LABEL) or \
                (res_preset.mj_execution_type == UiResourceDialog.PBS_LABEL and
                res_preset.j_execution_type == UiResourceDialog.PBS_LABEL):
            j_dialect = mj_dialect
        j_pbs = ConfFactory.get_pbs_conf(j_pbs_preset, pbs_params=j_env.pbs_params,
                                         dialect=j_dialect)
        jmj_python_env, jmj_libs_env = ConfFactory.get_env_conf(j_env)
        r_python_env, r_libs_env = ConfFactory.get_env_conf(mj_env, False, False)
        j_python_env, j_libs_env = ConfFactory.get_env_conf(j_env, False, False)

        # declare builders
        app = ConfBuilder(basic_conf)
        app.set_comm_name(CommType.app)\
            .set_python_env(mj_python_env)\
            .set_libs_env(mj_libs_env)
        app.conf.central_log = True

        delegator = None

        mj = ConfBuilder(basic_conf)
        mj.set_comm_name(CommType.multijob)\
            .set_python_env(r_python_env)\
            .set_libs_env(r_libs_env)
        mj.set_env_extras(mj_env)

        remote = None

        job = ConfBuilder(basic_conf)
        job.set_comm_name(CommType.job)\
            .set_python_env(j_python_env)\
            .set_libs_env(j_libs_env)
        job.set_env_extras(j_env)

        # set data with builders
        if mj_execution_type == UiResourceDialog.EXEC_LABEL:
            app.set_next_comm(CommType.multijob)\
                .set_out_comm(OutputCommType.exec_)
            mj.set_in_comm(InputCommType.socket)

        elif mj_execution_type == UiResourceDialog.DELEGATOR_LABEL:
            if mj_ssh_preset.use_tunneling:
                ssh_type = OutputCommType.ssh_tunnel
            else:
                ssh_type = OutputCommType.ssh
            app.set_next_comm(CommType.delegator)\
                .set_out_comm(ssh_type)\
                .set_ssh(mj_ssh)

            delegator = ConfBuilder(basic_conf)
            delegator.set_comm_name(CommType.delegator)\
                .set_next_comm(CommType.multijob)\
                .set_in_comm(InputCommType.std)\
                .set_python_env(mj_python_env)\
                .set_libs_env(mj_libs_env)
            delegator.set_env_extras(mj_env)
            if mj_remote_execution_type == UiResourceDialog.EXEC_LABEL:
                delegator.set_out_comm(OutputCommType.exec_)
                mj.set_in_comm(InputCommType.socket)
            elif mj_remote_execution_type == UiResourceDialog.PBS_LABEL:
                delegator.set_out_comm(OutputCommType.pbs)\
                    .set_pbs(mj_pbs)
                mj.set_in_comm(InputCommType.pbs)

        if j_execution_type == UiResourceDialog.EXEC_LABEL:
            mj.set_next_comm(CommType.job)\
                .set_out_comm(OutputCommType.exec_)
            job.set_in_comm(InputCommType.socket)
        elif j_execution_type == UiResourceDialog.REMOTE_LABEL:
            if j_ssh_preset.use_tunneling:
                ssh_type = OutputCommType.ssh_tunnel
            else:
                ssh_type = OutputCommType.ssh
            mj.set_next_comm(CommType.remote)\
                .set_out_comm(ssh_type)\
                .set_ssh(j_ssh)\
                .set_python_env(jmj_python_env)\
                .set_libs_env(jmj_libs_env)
            remote = ConfBuilder(basic_conf)
            remote.set_comm_name(CommType.remote)\
                .set_next_comm(CommType.job)\
                .set_in_comm(InputCommType.std)\
                .set_python_env(r_python_env)\
                .set_libs_env(r_libs_env)
            remote.set_env_extras(j_env)
            if j_remote_execution_type == UiResourceDialog.EXEC_LABEL:
                remote.set_out_comm(OutputCommType.exec_)
                job.set_in_comm(InputCommType.socket)
            elif j_remote_execution_type == UiResourceDialog.PBS_LABEL:
                remote.set_out_comm(OutputCommType.pbs)\
                    .set_pbs(j_pbs)
                job.set_in_comm(InputCommType.pbs)
        elif j_execution_type == UiResourceDialog.PBS_LABEL:
            mj.set_next_comm(CommType.job)\
                .set_out_comm(OutputCommType.pbs)\
                .set_pbs(j_pbs)
            job.set_in_comm(InputCommType.pbs)

        # configure paths
        exec_mj_exec_j = (mj_execution_type == UiResourceDialog.EXEC_LABEL and
                          j_execution_type == UiResourceDialog.EXEC_LABEL)
        exec_mj_remote_j = (mj_execution_type == UiResourceDialog.EXEC_LABEL and
                          j_execution_type == UiResourceDialog.REMOTE_LABEL)
        remote_mj_exec_j = (mj_execution_type == UiResourceDialog.DELEGATOR_LABEL and
                            j_execution_type == UiResourceDialog.EXEC_LABEL)
        remote_mj_remote_j = (mj_execution_type == UiResourceDialog.DELEGATOR_LABEL and
                              j_execution_type == UiResourceDialog.REMOTE_LABEL)

        app.set_paths_before_ssh(self.workspaces.get_path(), mj_preset)
        if exec_mj_exec_j:
            mj.set_paths_before_ssh(self.workspaces.get_path(), mj_preset)
            job.set_paths_before_ssh(self.workspaces.get_path(), mj_preset)
        elif remote_mj_exec_j:
            delegator.set_paths_on_ssh(mj_ssh_preset)
            mj.set_paths_on_ssh(mj_ssh_preset)
            job.set_paths_on_ssh(mj_ssh_preset)
        elif exec_mj_remote_j:
            delegator.set_paths_before_ssh(self.workspaces.get_path(), mj_preset, copy_ex_libs=True)
            mj.set_paths_before_ssh(self.workspaces.get_path(), mj_preset)
            remote.set_paths_on_ssh(mj_ssh_preset)
            job.set_paths_on_ssh(mj_ssh_preset)
        elif remote_mj_remote_j:
            delegator.set_paths_before_ssh(self.workspaces.get_path(), mj_preset, copy_ex_libs=True)
            mj.set_paths_on_ssh(mj_ssh_preset)
            remote.set_paths_on_ssh(mj_ssh_preset)
            job.set_paths_on_ssh(j_ssh_preset)

        if mj_remote_execution_type == UiResourceDialog.PBS_LABEL and \
           j_execution_type == UiResourceDialog.REMOTE_LABEL and \
           j_remote_execution_type == UiResourceDialog.PBS_LABEL:
            mj.conf.direct_communication = True
            remote.conf.direct_communication = True        
        # save to files
        with open(app.get_path(), "w") as app_file:
            CommunicatorConfigService.save_file(
                app_file, app.get_conf())
        if delegator:
            with open(delegator.get_path(), "w") as delegator_file:
                CommunicatorConfigService.save_file(
                    delegator_file, delegator.get_conf())
        with open(mj.get_path(), "w") as mj_file:
            CommunicatorConfigService.save_file(
                mj_file, mj.get_conf())
        if remote:
            with open(remote.get_path(), "w") as remote_file:
                CommunicatorConfigService.save_file(
                    remote_file, remote.get_conf())
        with open(job.get_path(), "w") as job_file:
            CommunicatorConfigService.save_file(
                job_file, job.get_conf())

        # build job configuration
        self._build_jobs_config(mj_name, an_name)

        # return app_config, it is always entry point for next operations
        return app.get_conf()

    def _build_jobs_config(self, mj_name, an_name):
        """Create jobs and associate them with individual configuration files."""
        jobs = {}
        mj_dir = Installation.get_mj_data_dir_static(mj_name, an_name)
        job_configs_path = os.path.join(Installation.get_config_dir_static(mj_name, an_name),
                                      ins.__ins_files__['job_configurations'])
        job_counter = 1

        try:
            analysis = Analysis.open_from_mj(mj_dir)
        except InvalidAnalysis:
            analysis = None

        def create_job(configuration_file):
            """Generate job name and create its configuration."""
            nonlocal job_counter
            name = JOB_NAME_LABEL + str(job_counter)
            data = {'configuration_file': configuration_file}
            jobs[name] = data
            job_counter += 1

        if analysis is not None:
            for file_path in analysis.selected_file_paths:
                if file_path.endswith('.yaml'):
                    # windows path workaround
                    rel_path_unix = '/'.join(file_path.split(os.path.sep))
                    create_job(rel_path_unix)

        # save job configurations to json
        with open(job_configs_path, 'w') as job_configs:
            json.dump(jobs, job_configs, indent=4, sort_keys=True)

    @staticmethod
    def gain_login(cc):
        if cc.ssh is not None and not cc.ssh.to_pc:
            dialog = SshPasswordDialog(None, cc.ssh)
            if dialog.exec_():
                return Users.get_preset_pwd2(config.__config_dir__, dialog.password, cc.ssh.key, cc.conf_long_id)


class ConfBuilder:
    def __init__(self, basic_conf):
        self.conf = copy.deepcopy(basic_conf)

    def set_comm_name(self, comm_name):
        self.conf.communicator_name = comm_name.value
        return self

    def set_next_comm(self, next_comm):
        self.conf.next_communicator = next_comm.value
        return self

    def set_in_comm(self, in_comm):
        self.conf.input_type = in_comm
        return self

    def set_out_comm(self, out_comm):
        self.conf.output_type = out_comm
        return self

    def set_ssh(self, ssh_conf):
        self.conf.ssh = ssh_conf
        return self

    def set_pbs(self, pbs_conf):
        self.conf.pbs = pbs_conf
        return self

    def set_python_env(self, python_env):
        self.conf.python_env = python_env
        return self

    def set_libs_env(self, libs_env):
        self.conf.libs_env = libs_env
        return self

    def set_env_extras(self, env):
        if self.conf.pbs:
            self.conf.pbs.pbs_params = env.pbs_params
        self.conf.flow_path = env.flow_path
        self.conf.cli_params = env.cli_params

    def get_conf(self):
        """
        Gets internal conf state.
        :return: CommunicatorConf object
        """
        return self.conf

    def get_path(self):
        """
        Get path to conf file.
        :return: Conf file path string.
        """
        path = Installation.get_config_dir_static(self.conf.mj_name, self.conf.an_name)
        file = self.conf.communicator_name + ".json"
        return os.path.join(path, file)

    def set_paths_before_ssh(self, workspace, mj, copy_ex_libs=False):
        self.conf.paths_config.home_dir = os.path.join(config.__config_dir__, BASE_DIR)
        self.conf.paths_config.work_dir = workspace
        self.conf.paths_config.app_dir = None
        self.conf.paths_config.ex_lib_path = EX_LIB_PATH
        self.conf.paths_config.copy_ex_libs = COPY_EX_LIBS if copy_ex_libs else None

    def set_paths_on_ssh(self, ssh):
        self.conf.paths_config.home_dir = None
        self.conf.paths_config.work_dir = None
        self.conf.paths_config.app_dir = ssh.remote_dir
        self.conf.paths_config.ex_lib_path = None
        self.conf.paths_config.copy_ex_libs = None

class ConfFactory:
    @staticmethod
    def get_pbs_conf(preset, with_socket=True, pbs_params=None, dialect=None):
        """
        Converts preset data to communicator config for PBS.
        :param preset: Preset data object from UI.
        :param with_socket: Defines if pbs communicates with socket, True in
        case of multijob, otherwise False.
        :return: PbsConf object
        """
        if not preset:
            return None
        pbs = PbsConfig()
        pbs.name = preset.name
        pbs.dialect = dialect
        pbs.queue = preset.queue
        pbs.walltime = preset.walltime
        pbs.nodes = str(preset.nodes)
        pbs.ppn = str(preset.ppn)
        pbs.memory = preset.memory
        pbs.infiniband = preset.infiniband
        pbs.with_socket = with_socket
        if pbs_params is not None:
            pbs.pbs_params = pbs_params
        return pbs

    @classmethod
    def get_ssh_conf(cls, preset, mj_name, an_name, long_id, is_remote=False):
        """
        Converts preset data to communicator config for SSH.
        :param preset: Preset data object from UI.
        :return: SshConf object
        """
        if not preset:
            return None
        ssh = SshConfig()
        ssh.name = preset.name
        ssh.host = preset.host
        ssh.port = preset.port
        ssh.uid = preset.uid
        ssh.to_pc = preset.to_pc
        ssh.to_remote = preset.to_remote

        # password
        if ssh.to_pc:
            dir = Installation.get_mj_data_dir_static(mj_name, an_name)
            users = Users(ssh.name, dir, config.__config_dir__, ssh.to_pc, ssh.to_remote)
            ssh.pwd, ssh.key = users.get_preset_pwd1(preset.key, is_remote, long_id)
        else:
            ssh.pwd = str(uuid.uuid4()) 
            ssh.key = str(uuid.uuid4()) 
            
        return ssh

    @staticmethod
    def get_env_conf(preset, install_job_libs=False, start_job_libs=False):
        """
        Converts preset data to communicator config for PythonEnv and LibsEnv.
        :param preset: Preset data object from UI.
        :param install_job_libs: True in case MultiJob or False in MultiJob
        and True in Remote if Remote exist.
        :param start_job_libs: True in case of Job.
        :return: PythonEnvConf object, LibsEnvConf object
        """
        python_env = PythonEnvConfig()
        python_env.python_exec = preset.python_exec
        python_env.scl_enable_exec = preset.scl_enable_exec
        python_env.module_add = preset.module_add

        libs_env = LibsEnvConfig()
        libs_env.install_job_libs = install_job_libs
        libs_env.start_job_libs = start_job_libs
        return python_env, libs_env
