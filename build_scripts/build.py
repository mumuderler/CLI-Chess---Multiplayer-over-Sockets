import PyInstaller.__main__
import os
import shutil

def build_executable(script_name, output_dir='dist'):
    print(f"Building {script_name}...")
    # Clean up previous build artifacts for this script
    if os.path.exists(f'build/{script_name.replace(".py", "")}'):
        shutil.rmtree(f'build/{script_name.replace(".py", "")}')
    if os.path.exists(f'{output_dir}/{script_name.replace(".py", "")}'):
        if os.path.isdir(f'{output_dir}/{script_name.replace(".py", "")}'):
            shutil.rmtree(f'{output_dir}/{script_name.replace(".py", "")}')
        else:
            os.remove(f'{output_dir}/{script_name.replace(".py", "")}')

    PyInstaller.__main__.run([
        script_name,
        '--onefile', # Create a single executable file
        '--name', script_name.replace('.py', ''), # Name of the executable
        '--distpath', output_dir, # Where to put the executable
        '--workpath', 'build', # Where to put all the temporary files
        '--specpath', 'spec', # Where to put the .spec file
        '--add-data', f'./ui.py{os.pathsep}.', # Add ui.py
        '--add-data', f'./shared.py{os.pathsep}.', # Add shared.py
        '--add-data', f'./ai_player.py{os.pathsep}.', # Add ai_player.py
        '--add-data', f'./export_image.py{os.pathsep}.', # Add export_image.py
    ])
    print(f"Finished building {script_name}.")

if __name__ == '__main__':
    # Ensure dist and build directories exist
    os.makedirs('dist', exist_ok=True)
    os.makedirs('build', exist_ok=True)
    os.makedirs('spec', exist_ok=True)

    build_executable('../server.py')
    build_executable('../client.py')

    print("\nBuild process complete. Executables are in the 'dist' directory.")