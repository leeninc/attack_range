import argparse
import re
import vagrant
import ansible_runner
import subprocess
import boto3
from python_terraform import *
from modules import logger

# need to set this ENV var due to a OSX High Sierra forking bug
# see this discussion for more details: https://github.com/ansible/ansible/issues/34056#issuecomment-352862252
os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES'

VERSION = 1


# could be improved by directly use extra-vars
def config_simulation(simulation_engine, simulation_technique, log):

    # Read in the ansible vars file
    with open('ansible/vars/vars.yml', 'r') as file:
        ansiblevars = file.read()

    # now set the simulation engine and mitre techniques to run
    if simulation_engine == "atomic_red_team":
        ansiblevars = re.sub(r'install_art: \w+', 'install_art: true', ansiblevars, re.M)
        log.info("execution simulation using engine: {0}".format(simulation_engine))

    if simulation_technique[0] != '' or len(simulation_technique) > 1:
        technique = "art_run_technique: " + str(simulation_technique)
        ansiblevars = re.sub(r'art_run_technique: .+', technique, ansiblevars, re.M)
        ansiblevars = re.sub(r'art_run_all_test: \w+', 'art_run_all_test: false', ansiblevars, re.M)
        log.info("executing specific ATT&CK technique ID: {0}".format(simulation_technique))
    else:
        ansiblevars = re.sub(r'art_run_all_test: \w+', 'art_run_all_test: true', ansiblevars, re.M)
        log.info("executing ALL Atomic Red Team ATT&CK techniques see: https://github.com/redcanaryco/atomic-red-team/tree/master/atomics".format(
            simulation_technique))

    # Write the file out again
    with open('ansible/vars/vars.yml', 'w') as file:
        file.write(ansiblevars)


def run_simulation(mode, simulation_engine, simulation_techniques, target, log):

    # read host file and replace the parameters
    with open('ansible/inventory/hosts.default', 'r') as file:
        hosts_file = file.read()

    # we need to change the port for ssh if we are running locally
    if mode == 'vagrant':
        # can be changed with the output of vagrant winrm-config [machine]
        hosts_file = hosts_file.replace('ansible_ssh_port=5986', 'ansible_ssh_port=5985')
        hosts_file = hosts_file.replace(
            'ansible_ssh_user=Administrator', 'ansible_ssh_user = vagrant')
        hosts_file = hosts_file.replace(
            'ansible_ssh_pass=myTempPassword123', 'ansible_ssh_pass = vagrant')
        hosts_file = hosts_file.replace('PUBLICIP', '127.0.0.1')
    if mode == 'terraform':
        hosts_file = hosts_file.replace('PUBLICIP', target)

    # write hosts file to run from
    with open('ansible/inventory/hosts', 'w') as file:
        file.write(hosts_file)

    # execute atomic red team simulation
    if simulation_engine == "atomic_red_team":
        r = ansible_runner.run(private_data_dir='.attack_range/',
                               inventory=os.path.dirname(os.path.realpath(
                                   __file__)) + '/ansible/inventory/hosts',
                               roles_path="../roles",
                               playbook=os.path.dirname(os.path.realpath(__file__)) + '/ansible/playbooks/atomic_red_team.yml',
                               verbosity=0)

        if r.status == "successful":
            log.info("successfully executed technique ID {0} against target: {1}".format(simulation_techniques, target))
        else:
            log.error("failed to executed technique ID {0} against target: {1}".format(simulation_techniques, target))
            sys.exit(1)

def prep_ansible():
    # prep ansible for configuration
    # lets configure the passwords for ansible before we run any operations
    #    try:
    f = open("terraform/terraform.tfvars", "r")
    contents = f.read()

    win_password = re.findall(r'^win_password = \"(.+)\"', contents, re.MULTILINE)
    win_username = re.findall(r'^win_username = \"(.+)\"', contents, re.MULTILINE)

    # Read in the ansible vars file
    with open('ansible/vars/vars.yml.default', 'r') as file:
        ansiblevars = file.read()

    # Replace the username and password
    ansiblevars = ansiblevars.replace('USERNAME', win_username[0])
    ansiblevars = ansiblevars.replace('PASSWORD', win_password[0])

    # Write the file out again
    with open('ansible/vars/vars.yml', 'w') as file:
        file.write(ansiblevars)

#        log.info(
#            "setting windows username: {0} from terraform/terraform.tfvars file".format(win_username))
#        log.info(
#            "setting windows password: {0} from terraform/terraform.tfvars file".format(win_password))
#    except e:
    #        log.error("make sure that ansible/host.default contains the windows username and password.\n" +
    #              "We were not able to set it automatically")



def vagrant_mode(action, log):

    vagrantfile = 'vagrant/'

    if action == "build":
        log.info("building splunk-server and windows10 workstation boxes WARNING MAKE SURE YOU HAVE 8GB OF RAM free otherwise you will have a bad time")
        log.info("[action] > build\n")
        v1 = vagrant.Vagrant(vagrantfile, quiet_stdout=False)
        v1.up(provision=True)
        log.info("attack_range has been built using vagrant successfully")

    if action == "destroy":
        log.info("[action] > destroy\n")
        v1 = vagrant.Vagrant(vagrantfile, quiet_stdout=False)
        v1.destroy()
        log.info("attack_range has been destroy using vagrant successfully")


def attack_simulation(mode, target, simulation_engine, simulation_techniques, log):
    if mode == 'vagrant':
        v1 = vagrant.Vagrant('vagrant/', quiet_stdout=False)
        status = v1.status()
        # Check if target exist and if it is running
        check_targets_running_vagrant(target, log)
        config_simulation(simulation_engine, simulation_techniques, log)
        run_simulation('vagrant', simulation_engine, simulation_techniques, target, log)

    if mode == 'terraform':
        target_IP = check_targets_running_terraform(target, log)
        config_simulation(simulation_engine, simulation_techniques, log)
        run_simulation('terraform', simulation_engine, simulation_techniques, target_IP, log)

# @Jose the beginning part of the function needs to be changed to the common configuration file
def check_targets_running_terraform(target, log):
    with open('terraform/terraform.tfvars', 'r') as file:
        terraformvars = file.read()

    pattern = 'key_name = \"([^\"]*)'
    a = re.search(pattern, terraformvars)
    client = boto3.client('ec2')
    response = client.describe_instances(
        Filters=[
            {
                'Name': "tag:Name",
                'Values': [target]
            },
            {
                'Name': "key-name",
                'Values': [a.group(1)]
            }
        ]
    )

    if len(response['Reservations']) == 0:
        log.error(target + ' not found as AWS EC2 instance.')
        sys.exit(1)

    # iterate through reservations and instances
    found_running_instance = False
    for reservation in response['Reservations']:

        for instance in reservation['Instances']:
            if instance['State']['Name'] == 'running':
                found_running_instance = True
                return instance['NetworkInterfaces'][0]['Association']['PublicIp']

    if not found_running_instance:
        log.error(target + ' not running.')
        sys.exit(1)


def check_targets_running_vagrant(target, log):
    v1 = vagrant.Vagrant('vagrant/', quiet_stdout=False)
    status = v1.status()

    found_box = False
    for stat in status:
        if stat.name == target:
            found_box = True
            if not (stat.state == 'running'):
                log.error(target + ' not running.')
                sys.exit(1)
            break
    if not found_box:
        log.error(target + ' not found as vagrant box.')
        sys.exit(1)


# def get_target_ips_vagrant(targets):
#     ip_array = []
#
#     for target in targets:
#         p = subprocess.Popen(['vagrant', 'winrm-config', target],
#                              cwd='vagrant/', stdout=subprocess.PIPE)
#         (result, error) = p.communicate()
#         print(result)


def terraform_mode(action, log):
    if action == "build":
        log.info("[action] > build\n")
        t = Terraform(working_dir='terraform')
        return_code, stdout, stderr = t.apply(
            capture_output='yes', skip_plan=True, no_color=IsNotFlagged)
        log.info("attack_range has been built using terraform successfully")

    if action == "destroy":
        log.info("[action] > destroy\n")
        t = Terraform(working_dir='terraform')
        return_code, stdout, stderr = t.destroy(capture_output='yes', no_color=IsNotFlagged)
        log.info("attack_range has been destroy using terraform successfully")



if __name__ == "__main__":
    # grab arguments
    parser = argparse.ArgumentParser(
        description="starts a attack range ready to collect attack data into splunk")
    parser.add_argument("-m", "--mode", required=True, default="terraform", choices=['vagrant', 'terraform'],
                        help="mode of operation, terraform/vagrant, please see configuration for each at: https://github.com/splunk/attack_range")
    parser.add_argument("-a", "--action", required=True, default="build", choices=['build', 'destroy', 'simulate'],
                        help="action to take on the range, defaults to \"build\", build/destroy/simulate allowed")
    parser.add_argument("-t", "--target", required=False,
                        help="target for attack simulation. For mode vagrant use name of the vbox. For mode terraform use the name of the aws EC2 name")
    parser.add_argument("-se", "--simulation_engine", required=False, choices=['atomic_red_team'], default="atomic_red_team",
                        help="please select a simulation engine, defaults to \"atomic_red_team\"")
    parser.add_argument("-st", "--simulation_technique", required=False, type=str, default="",
                        help="comma delimited list of MITRE ATT&CK technique ID to simulate in the attack_range, example: T1117, T1118, requires --simulation flag")
    parser.add_argument("-o", "--output", required=False, default="attack_range.log",
                        help="path to log file from the output of the range execution")
    parser.add_argument("-v", "--version", required=False,
                        help="shows current attack_range version")

    # parse them
    args = parser.parse_args()
    ARG_VERSION = args.version
    mode = args.mode
    action = args.action
    target = args.target
    simulation_engine = args.simulation_engine
    simulation_techniques = [str(item) for item in args.simulation_technique.split(',')]

    print("""
    starting program loaded for mode - B1 battle droid

      ||/__'`.
      |//()'-.:
      |-.||
      |o(o)
      |||\\\  .==._
      |||(o)==::'
       `|T  ""
        ()
        |\\
        ||\\
        ()()
        ||//
        |//
       .'=`=.
        """)

    log = logger.setup_logging(args.output, "INFO")
    log.info("INIT - Attack Range v" + str(VERSION))

    if ARG_VERSION:
        # log.info("version: {0}".format(VERSION))
        sys.exit(1)

    # to do: define which arguments are needed for build and which for simulate

    # lets process modes
    if mode == "vagrant":
        log.info("[mode] > vagrant")
        if action == "build" or action == "destroy":
            vagrant_mode(action, log)
        else:
            attack_simulation('vagrant', target, simulation_engine, simulation_techniques, log)

    elif mode == "terraform":
        prep_ansible()
        log.info("[mode] > terraform ")
        if action == "build" or action == "destroy":
            terraform_mode(action, log)
        else:
            attack_simulation('terraform', target, simulation_engine, simulation_techniques, log)

    else:
        log.error("incorrect mode, please set flag --mode to \"terraform\" or \"vagrant\"")
        sys.exit(1)