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


def check_paths(paths):
    for path in paths:
        if os.path.isdir(path):
            answer = input(
                f'{path} directory already exist in the current path, do you want to remove it? (y/n)')
            if answer == 'y':
                shutil.rmtree(path, ignore_errors=True)
            else:
                print('stopping the script')
                return False
    return True


def regex_search(regex, string):
    search = re.search(regex, string)
    if search is None:
        return None
    else:
        return search.group(1)


def check_none(paths):
    for path in paths:
        if path is None:
            print('Make sure the values in params.json are correct')
            print('Stopping the script')
            return True
    return False


def copy(source_path, dest_path):
    if os.path.isdir(source_path):
        shutil.copytree(source_path, dest_path)
    else:
        os.makedirs(dest_path)
        shutil.copy(source_path, dest_path)


def execute():
    load_params()
    source_repo_path = regex_search(r'([^\/]+).git', source_repo_url)
    dest_repo_path = regex_search(r'([^\/]+).git', dest_repo_url)
    base_source_path = regex_search(r'^(.*?)\/', path_to_migrate)
    # checks
    if check_none([source_repo_path, dest_repo_path, base_source_path]) \
            or not check_paths([source_repo_path, dest_repo_path]):
        return
    # migration process
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
    copy(path_to_migrate, path_in_dest)
    print(f'step 6/11: delete {base_source_path}')
    shutil.rmtree(base_source_path, ignore_errors=True)
    print(f'step 7/11: git add . (in source repo)')
    source_repo.execute(['git', 'add', '.'])
    print(f'step 8/11: git commit (in source repo)')
    source_repo.execute(['git', 'commit', '-m', f'"prepare {path_to_migrate} for migration"'])
    os.chdir(f'../{dest_repo_path}')
    print(f'step 9/11: add source repo as remote to dest repo')
    dest_repo.execute(['git', 'remote', 'add', 'src', f'../{source_repo_path}'])
    print(f'step 10/11: pull changes from source repo to dest repo')
    dest_repo.execute(['git', 'pull', 'src', 'master', '--allow-unrelated-histories'])
    print(f'\nNow its time to open {dest_repo_path} in your ide and make it work!')
    print('Next steps should be fixing the imports and make the project compile.')
    print(f'Afterwards push the changes to {dest_repo_url} and merge "as is" without Squash!!')
    print('for more information check '
          'https://github.com/redislabsdev/SM-UI-Refresh/blob/develop/automation/readme/file-migration.md')


if __name__ == '__main__':
    execute()
