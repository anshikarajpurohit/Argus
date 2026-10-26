import {spawnSync} from 'node:child_process';
const result=spawnSync(process.execPath,['--experimental-vm-modules','node_modules/jest/bin/jest.js','--runInBand',...process.argv.slice(2)],{stdio:'inherit',env:process.env});process.exit(result.status??1);
