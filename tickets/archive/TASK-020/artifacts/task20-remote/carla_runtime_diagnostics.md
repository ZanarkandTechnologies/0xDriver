# CARLA Runtime Diagnostics

## Summary
- route_log: CARLA did not open port 20000 within 120s
- carla_exit_status_after_xdg: 1
- carla_exit_status_opengl: 1

## NVIDIA
NVIDIA H100 80GB HBM3, 580.126.09, 81559 MiB

## Vulkan Default Devices
	deviceType         = PHYSICAL_DEVICE_TYPE_CPU
	deviceName         = llvmpipe (LLVM 15.0.7, 256 bits)
	driverName         = llvmpipe

## NVIDIA Vulkan ICD
ERROR: [Loader Message] Code 0 : loader_scanned_icd_add: Could not get 'vkCreateInstance' via 'vk_icdGetInstanceProcAddr' for ICD libGLX_nvidia.so.0
Cannot create Vulkan instance.
This problem is often caused by a faulty installation of the Vulkan driver or attempting to use a GPU that does not support Vulkan.
ERROR at ./vulkaninfo/vulkaninfo.h:649:vkCreateInstance failed with ERROR_INCOMPATIBLE_DRIVER

## Route Log
CARLA did not open port 20000 within 120s: [Errno 111] Connection refused

## CARLA Launch Logs
### /workspace/artifacts/task20/carla/diagnostic-after-xdg.log
4.26.2-0+++UE4+Release-4.26 522 0
Disabling core dumps.
STATUS:1

### /workspace/artifacts/task20/carla/diagnostic-opengl.log
4.26.2-0+++UE4+Release-4.26 522 0
Disabling core dumps.
STATUS:1

### /workspace/artifacts/task20/carla/diagnostic-ldpath.log
4.26.2-0+++UE4+Release-4.26 522 0
Disabling core dumps.
STATUS:1

