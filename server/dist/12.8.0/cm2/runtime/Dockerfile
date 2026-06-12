ARG IMAGE_NAME
FROM ${IMAGE_NAME}:12.8.0-base-cm2 as base

ENV NV_CUDA_LIB_VERSION 12.8.0-1

FROM base as base-amd64

ENV NV_NVTX_VERSION 12.8.55-1
ENV NV_LIBNPP_VERSION 12.3.3.65-1
ENV NV_LIBNPP_PACKAGE libnpp-12-8-${NV_LIBNPP_VERSION}
ENV NV_LIBCUBLAS_VERSION 12.8.3.14-1
FROM base-${TARGETARCH}

ARG TARGETARCH

LABEL maintainer "NVIDIA CORPORATION <sw-cuda-installer@nvidia.com>"

RUN yum install -y \
    cuda-libraries-12-8-${NV_CUDA_LIB_VERSION} \
    cuda-nvtx-12-8-${NV_NVTX_VERSION} \
    ${NV_LIBNPP_PACKAGE} \
    libcublas-12-8-${NV_LIBCUBLAS_VERSION} \
    && yum clean all \
    && rm -rf /var/cache/yum/*

# Add entrypoint items
COPY entrypoint.d/ /opt/nvidia/entrypoint.d/
COPY nvidia_entrypoint.sh /opt/nvidia/
ENV NVIDIA_PRODUCT_NAME="CUDA"
ENTRYPOINT ["/opt/nvidia/nvidia_entrypoint.sh"]