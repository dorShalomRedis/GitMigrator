import json
import git
import os
import git_filter_repo
import shutil
import re


def load_params():
    global source_repo_url, dest_repo_url, paths_to_migrate, paths_in_dest
    with open('params.json', 'r') as json_file:
        params = json.load(json_file)
        source_repo_url = params['source_repo_url']
        dest_repo_url = params['dest_repo_url']
        paths_to_migrate = params['paths_to_migrate']
        paths_in_dest = params['paths_in_dest']


def check_dirs_exist(paths):
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


def check_none(paths):
    for path in paths:
        if path is None:
            print('Make sure the values in params.json are correct')
            print('Stopping the script')
            return True
    return False


def check_paths():
    if len(paths_to_migrate) != len(paths_in_dest):
        print('Number of paths_to_migrate does not match paths_in_dest')
        print('Stopping the script')
        return True
    return False


def regex_search(regex, string):
    search = re.search(regex, string)
    if search is None:
        return None
    else:
        return search.group(1)


def copy():
    for i in range(0, len(paths_to_migrate)):
        if os.path.isdir(paths_to_migrate[i]):
            shutil.copytree(paths_to_migrate[i], paths_in_dest[i])
        else:
            dest_path = paths_in_dest[i] if os.path.isdir(paths_in_dest[i]) else paths_in_dest[i].rsplit('/', 1)[0]
            if not os.path.exists(dest_path):
                os.makedirs(dest_path)
            shutil.copy(paths_to_migrate[i], paths_in_dest[i])


def filter_paths():
    args_list = ['--force']
    global base_source_paths
    base_source_paths = set()
    for path_to_migrate in paths_to_migrate:
        base_source_paths.add(regex_search(r'^(.*?)\/', path_to_migrate))
        args_list.append('--path')
        args_list.append(path_to_migrate)
    args = git_filter_repo.FilteringOptions.parse_args(args_list)
    path_filter = git_filter_repo.RepoFilter(args)
    path_filter.run()


def execute():
    load_params()
    source_repo_path = regex_search(r'([^\/]+).git', source_repo_url)
    dest_repo_path = regex_search(r'([^\/]+).git', dest_repo_url)
    # checks
    if check_none([source_repo_path, dest_repo_path]) \
            or not check_dirs_exist([source_repo_path, dest_repo_path]):
        return
    # migration process
    print(f'step 1/10: clone {source_repo_url}.')
    source_repo = git.Git(source_repo_path)
    source_repo.clone(source_repo_url)
    print(f'step 2/10: clone {dest_repo_url}.')
    dest_repo = git.Git(dest_repo_path)
    dest_repo.clone(dest_repo_url)
    print(f'step 3/10: remove remote')
    source_repo.execute(['git', 'remote', 'rm', 'origin'])
    os.chdir(source_repo_path)  # filter occurs in cwd
    print(f'step 4/10: filter desired paths history and delete the rest of the repo.')
    filter_paths()
    print(f'step 5/10: Move files from source paths to dest paths')
    copy()
    print(f'step 6/10: delete old trees')
    [shutil.rmtree(path, ignore_errors=True) for path in base_source_paths]
    print(f'step 7/10: git add . (in source repo)')
    source_repo.execute(['git', 'add', '.'])
    print(f'step 8/10: git commit (in source repo)')
    source_repo.execute(['git', 'commit', '-m', f'"prepare for migration"'])
    os.chdir(f'../{dest_repo_path}')
    print(f'step 9/10: add source repo as remote to dest repo')
    dest_repo.execute(['git', 'remote', 'add', 'src', f'../{source_repo_path}'])
    print(f'step 10/10: pull changes from source repo to dest repo')
    dest_repo.execute(['git', 'pull', 'src', 'master', '--allow-unrelated-histories', '--no-ff'])
    print(f'\nNow its time to open {dest_repo_path} in your ide and make it work!')
    print('Next steps should be fixing the imports and make the project compile.')
    print(f'Afterwards push the changes to {dest_repo_url} and merge "as is" without Squash!!')
    print('for more information check '
          'https://github.com/redislabsdev/SM-UI-Refresh/blob/develop/automation/readme/file-migration.md')


if __name__ == '__main__':
    execute()
