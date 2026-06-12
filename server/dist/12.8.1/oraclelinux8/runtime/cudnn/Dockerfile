ARG IMAGE_NAME
FROM ${IMAGE_NAME}:12.8.1-runtime-oraclelinux8 AS base

ENV PKG_CMD=yum

FROM base AS base-amd64

ENV NV_CUDNN_VERSION=9.8.0.87-1
ENV NV_CUDNN_PACKAGE=libcudnn9-cuda-12-${NV_CUDNN_VERSION}

FROM base AS base-arm64

ENV NV_CUDNN_VERSION=9.8.0.87-1
ENV NV_CUDNN_PACKAGE=libcudnn9-cuda-12-${NV_CUDNN_VERSION}


FROM base-${TARGETARCH}

ARG TARGETARCH

LABEL maintainer="NVIDIA CORPORATION <sw-cuda-installer@nvidia.com>"

LABEL com.nvidia.cudnn.version="${NV_CUDNN_VERSION}"

RUN ${PKG_CMD} install -y \
    ${NV_CUDNN_PACKAGE} \
    && ${PKG_CMD} clean all \
    && rm -rf /var/cache/yum/*