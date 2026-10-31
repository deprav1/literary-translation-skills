"""Use the owner's configured local route without exposing credentials to CLI arguments."""
from __future__ import annotations

import argparse
import json
import os
import tomllib
from pathlib import Path
from urllib.parse import urlsplit

import sol_micro_trial as trial


def configured_route():
    config = tomllib.loads((Path.home()/'.codex/config.toml').read_text(encoding='utf8'))
    provider = config['model_providers'][config['model_provider']]
    url = urlsplit(provider['base_url'])
    assert url.scheme == 'http' and url.hostname in ['localhost', '127.0.0.1']
    assert provider['wire_api'] == 'responses' and not provider.get('requires_openai_auth', False)
    # Secrets stay in subprocess environment; never persist or print these values.
    env = os.environ.copy()
    env['SOL_MICRO_LOCAL_TOKEN'] = provider['experimental_bearer_token']
    headers = {}
    for i, (name, value) in enumerate(provider.get('http_headers', {}).items()):
        key = 'SOL_MICRO_HEADER_'+str(i); env[key] = value; headers[name] = key
    header_toml = ','.join(json.dumps(k)+'='+json.dumps(v) for k, v in headers.items())
    definition = ('{name="configured local route",base_url='+json.dumps(provider['base_url'])+
        ',wire_api="responses",env_key="SOL_MICRO_LOCAL_TOKEN",requires_openai_auth=false,'
        'supports_websockets=false,env_http_headers={'+header_toml+'}}')
    return ['--config', 'model_provider="sol_micro_local"', '--config',
            'model_providers.sol_micro_local='+definition], env


def run(root):
    amendment = trial.read(trial.BASE/'transport-amendment.json')
    assert amendment['adapter_sha256'] == trial.sha(Path(__file__).read_bytes())
    assert amendment['original_preregistration_sha256'] == trial.sha((trial.BASE/'preregistration.json').read_bytes())
    extra, env = configured_route()
    original = trial.subprocess.run

    def routed(args, **kwargs):
        assert args[1] == 'exec' and args[-1] == '-' and kwargs.get('input')
        return original(args[:-1]+extra+args[-1:], env=env, **kwargs)

    trial.subprocess.run = routed
    try:
        trial.run(root)
    finally:
        trial.subprocess.run = original


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    args = parser.parse_args()
    run(args.workspace.resolve())
