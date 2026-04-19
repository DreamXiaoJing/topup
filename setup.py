# !/usr/bin/env python
# -*- coding: utf-8 -*-
"""TopUp - 统一充值SDK"""

from setuptools import setup, find_packages

# 读取README
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="topup",
    version="0.1.0",
    author="weiqingwei",
    author_email="1361735164@qq.com",
    description="统一充值SDK",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DreamXiaoJing/topup",  # 可选：填写GitHub/Gitee地址
    license="MIT",

    # 包发现
    packages=find_packages(),

    # Python版本
    python_requires=">=3.8",

    # 依赖
    install_requires=[
        "curl_cffi>=0.14.0",
    ],

    # 分类
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Office/Business :: Financial",
    ],
    zip_safe=False,
)
