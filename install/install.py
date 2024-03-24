import tomllib
import pathlib
import asyncio


async def install(parent_cfg: dict) -> dict:
    config_file = pathlib.Path('/'.join(__file__.split('/')[:-2])) / 'config/config.toml'
    cfg = {}
    out = {}
    with config_file.open('rb') as f:
        cfg = tomllib.load(f)
    requirements = cfg.get('setup', {}).get('requirements')
    if requirements:
        out['requirements'] = requirements
    run = cfg.get('setup', {}).get('run')
    if run:
        for idx, entry in run.items():
            entry = entry.replace('%base%', parent_cfg.get('folder', {}).get('base', ''))
            run[idx] = entry.replace('%git%', parent_cfg.get('folder', {}).get('git', ''))
        out['run'] = run
    bash_profile = pathlib.Path.home() / '.bash_profile'
    bak = pathlib.Path.home() / '.bash_profile.lcars.bak'
    if bash_profile.exists() and not bak.exists():
        p = await asyncio.subprocess.create_subprocess_shell(f'cp {bash_profile} {bak}', 
                                                         stderr=asyncio.subprocess.PIPE, 
                                                         stdout=asyncio.subprocess.PIPE)
        await p.wait()
    with bash_profile.open('w') as f:
        f.write('clear\nlcars-status\n')    
    return out
