# System Tool

Provides hardware diagnostic services, resource usages, and system application execution.

## Features

- **Battery**: Real-time capacity percentage, charging status, and remaining runtime.
- **CPU**: Physical and logical cores, clock speed, and current utilization percentage.
- **RAM**: Memory capacity, consumption, availability, and utilization index.
- **Disk**: Local partition sizes, usage statistics, and free storage capacities.
- **Processes**: Retrieve actively running OS processes sorted by resource footprints.
- **Open / Close Apps**: Launch and terminate desktop programs safely with input parameters validation.

## Endpoints

- `GET /system/cpu`: Physical layout and real-time CPU metric.
- `GET /system/battery`: Charging indicator and capacity value.
- `GET /system/memory`: Internal physical memory usage.
- `GET /system/disk`: Active partition details.
- `GET /system/processes`: Currently running processes list.
- `POST /system/open`: Safe execute a desktop application.
- `POST /system/close`: Terminate active tasks matching description name.
