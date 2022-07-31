import json
import git
import os
import git_filter_repo
import shutil
import re



def load_params():
    global source_repo_url, dest_repo_url, path_to_migrate, path_in_dest
    with open('params.json', 'r') as json_file:
        params = json.load(json_file)
        source_repo_url = params['source_repo_url']
        dest_repo_url = params['dest_repo_url']
        path_to_migrate = params['path_to_migrate']
        path_in_dest = params['path_in_dest']

def execute():
    load_params()
    source_repo_path = re.search(r'([^\/]+).git', source_repo_url).group(1)
    dest_repo_path = re.search(r'([^\/]+).git', dest_repo_url).group(1)
    base_source_path = re.search(r'^(.*?)\/', path_to_migrate).group(1)
    print(f'step 1/11: clone {source_repo_url}.')
    source_repo = git.Git(source_repo_path)
    source_repo.clone(source_repo_url)
    print(f'step 2/11: clone {dest_repo_url}.')
    dest_repo = git.Git(dest_repo_path)
    dest_repo.clone(dest_repo_url)
    print(f'step 3/11: remove remote')
    source_repo.execute(['git', 'remote', 'rm', 'origin'])
    os.chdir(source_repo_path)  # filter occurs in cwd
    print(f'step 4/11: filter {path_to_migrate} history and delete the rest of the repo.')
    args = git_filter_repo.FilteringOptions.parse_args(['--path', path_to_migrate, '--force'])
    path_filter = git_filter_repo.RepoFilter(args)
    path_filter.run()
    print(f'step 5/11: Move files from {path_to_migrate} to {path_in_dest}')
    os.makedirs(path_in_dest)
    shutil.move(path_to_migrate, path_in_dest)
    print(f'step 6/11: delete {base_source_path}')
    shutil.rmtree(base_source_path)
    print(f'step 7/11: git add . (in source repo)')
    source_repo.execute(['git', 'add', '.'])
    print(f'step 8/11: git commit (in source repo)')
    source_repo.execute(['git', 'commit', '-m', f'"prepare {path_to_migrate} for migration"'])
    os.chdir(f'../{dest_repo_path}')
    print(f'step 9/11: add source repo as remote to dest repo')
    dest_repo.execute(['git', 'remote', 'add', 'src', f'../{source_repo_path}'])
    print(f'step 10/11: pull changes from source repo to dest repo')
    dest_repo.execute(['git', 'pull', 'src', 'master', '--allow-unrelated-histories'])
    print(f'step 11/11: Now its time to open {dest_repo_path} in your ide and make it work')


if __name__ == '__main__':
    execute()
