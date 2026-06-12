ARG IMAGE_NAME
FROM ${IMAGE_NAME}:12.8.0-runtime-amzn2023 as base

FROM base as base-amd64

ENV NV_CUDA_LIB_VERSION 12.8.0-1
ENV NV_NVPROF_VERSION 12.8.57-1
ENV NV_NVPROF_DEV_PACKAGE cuda-nvprof-12-8-${NV_NVPROF_VERSION}
ENV NV_CUDA_CUDART_DEV_VERSION 12.8.57-1
ENV NV_NVML_DEV_VERSION 12.8.55-1
ENV NV_LIBCUBLAS_DEV_VERSION 12.8.3.14-1
ENV NV_LIBNPP_DEV_VERSION 12.3.3.65-1
ENV NV_LIBNPP_DEV_PACKAGE libnpp-devel-12-8-${NV_LIBNPP_DEV_VERSION}
ENV NV_CUDA_NSIGHT_COMPUTE_VERSION 12.8.0-1
ENV NV_CUDA_NSIGHT_COMPUTE_DEV_PACKAGE cuda-nsight-compute-12-8-${NV_CUDA_NSIGHT_COMPUTE_VERSION}



FROM base-${TARGETARCH}

ARG TARGETARCH

LABEL maintainer "NVIDIA CORPORATION <sw-cuda-installer@nvidia.com>"

RUN yum install -y \
    make \
    findutils \
    cuda-command-line-tools-12-8-${NV_CUDA_LIB_VERSION} \
    cuda-libraries-devel-12-8-${NV_CUDA_LIB_VERSION} \
    cuda-minimal-build-12-8-${NV_CUDA_LIB_VERSION} \
    cuda-cudart-devel-12-8-${NV_CUDA_CUDART_DEV_VERSION} \
    ${NV_NVPROF_DEV_PACKAGE} \
    cuda-nvml-devel-12-8-${NV_NVML_DEV_VERSION} \
    libcublas-devel-12-8-${NV_LIBCUBLAS_DEV_VERSION} \
    ${NV_LIBNPP_DEV_PACKAGE} \
    ${NV_CUDA_NSIGHT_COMPUTE_DEV_PACKAGE} \
    && yum clean all \
    && rm -rf /var/cache/yum/*

ENV LIBRARY_PATH /usr/local/cuda/lib64/stubs