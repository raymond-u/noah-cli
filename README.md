# Noah

Noah is a project management tool specifically designed for bioinformatics projects. It enables reproducible analysis of large datasets, making it effortless to share and collaborate with others.

[![PyPI version](https://badge.fury.io/py/noah-cli.svg)](https://badge.fury.io/py/noah-cli)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

# Features

- [x] A human-readable configuration file
- [x] Git integration
- [x] Guaranteed reproducibility and portability
- [ ] Managing data, containers, and workflows, all in one place

# Installation

The easiest way to install Noah is to use pip:

```bash
pip install noah-cli
```

# Quickstart

To get started with Noah, use the `noah init` command to create a new project:

```bash
noah init my_project # This will by default create a Git repository
cd my_project
```

To add a new dataset to your project, use the `noah add` command:

```bash
noah add SRP123456 # ENCSR123ABC, GSE123456, etc. are also supported
```

You can also add privately hosted datasets:

```bash
noah add me@some_host:path/to/my_dataset ftp://ftp.example.com/another_dataset
```

If you share your project with others, they can easily retrieve the datasets you added:

```bash
noah install
```

For more information, please refer to [examples](examples/README.md).

# License

This software is licensed under the MIT license. See [LICENSE](LICENSE) for more details.
