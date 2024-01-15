import subprocess

shell_script_path = './autoresell.sh'
resellcount = input()

subprocess.run(['sh',shell_script_path,resellcount])