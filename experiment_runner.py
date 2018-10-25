from subprocess import STDOUT, check_output, Popen, PIPE, TimeoutExpired
import signal
import tempfile
import shutil
import os
from contextlib import contextmanager

@contextmanager
def cwd(path):
    oldpwd=os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(oldpwd)

def create_env():
    d = tempfile.mkdtemp()
    for executable in ['sp', 'walksat', 'merge', 'verify']:
        assert os.path.exists(executable), executable
        shutil.copy(executable, d)
    return d

def run_sat(path, timeout):
    with Popen('./sp -%%1 -l%s' % path, shell=True, stdout=PIPE, preexec_fn=os.setsid) as process:
        try:
            sat_output = process.communicate(timeout=timeout)[0]
        except TimeoutExpired:
            os.killpg(process.pid, signal.SIGINT) # send signal to the process group
            os.killpg(process.pid, signal.SIGKILL) # send signal to the process group
            sat_output = process.communicate()[0]

    sat_output = str(sat_output)
    return sat_output

def run_xor_trial(num_vars, density, xor_num_vars=2, timeout=60):
    d = create_env()
    output = check_output('''python graph_gen/generate_xor_cnf.py \
        --num_variables=%d \
        --xor_density=%0.2f \
        --xor_num_vars=%d \
        --cnf_file_path=%s/xor.cnf \
        ''' % (num_vars, density, xor_num_vars, d), shell=True)

    with cwd(d):
        sat_output = run_sat('xor.cnf', timeout)
        assignment_found = 'ASSIGNMENT FOUND' in sat_output
        shutil.rmtree(d)
        return assignment_found

def run_k_color_trial(num_nodes, edge_density, num_colors, timeout=60):
    d = create_env()
    output = check_output('''python graph_gen/generate_k_coloring_cnf.py \
        --num_nodes=%d \
        --edge_density=%0.2f \
        --num_colors=%d \
        --cnf_file_path=%s/graph.cnf \
        ''' % (num_nodes, edge_density, num_colors, d), shell=True)

    with cwd(d):
        sat_output = run_sat('graph.cnf', timeout)
        assignment_found = 'ASSIGNMENT FOUND' in sat_output
        shutil.rmtree(d)
        return assignment_found

print(run_xor_trial(num_vars=20, density=0.1, timeout=10))
print(run_k_color_trial(num_nodes=20, edge_density=1, num_colors=5, timeout=10))
