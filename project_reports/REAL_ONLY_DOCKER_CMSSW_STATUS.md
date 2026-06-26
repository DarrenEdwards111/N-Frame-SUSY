# Real-Only Docker/CMSSW Status

Date: 2026-06-08

Docker is running and the existing CMS Open Data image `cmsopendata/cmssw_10_6_30-slc7_amd64_gcc700:latest` is available locally.

Checks completed:

- Docker daemon: running
- CMSSW image starts: yes
- `/data` mount to real CMS MiniAOD folder: yes
- `/work` mount to CMSSW extraction package: yes
- `cmsRun` available inside the container: yes
- Extraction script smoke test: passed on 10 real MET events
- New huge image pulled: no

The smoke test also confirmed the extended analyzer compiles with real MiniAOD fields for primary vertices, packed candidates, secondary vertices and max b-tag discriminator.

Log: `D:\Gamer File\My Work\The PhD\Extra\Nframe\nframe_cms_stage2_event_boundary\results\logs\real_only_docker_cmssw_status.log`
