# Noah

Noah is a project management tool specifically designed for bioinformatics projects. It enables reproducible analysis of large datasets, making it effortless to share and collaborate with others.

# Features

- [x] A human-readable configuration file
- [x] Automated retrieval of data from public databases
- [ ] Managing data, containers, and workflows, all in one place

# Installation

The easiest way to install Noah is to use pip:

```bash
pip install noah-cli
```

# Quickstart

To get started with Noah, you can use the `noah init` command to create a new project:

```bash
noah init my_project # This will by default create a Git repository in my_project
cd my_project
```

To add a new dataset to your project, you can use the `noah add` command:

```bash
noah add SRP123456 # ENCSR123ABC, GSE123456, etc. are also supported
```

You can also add privately hosted datasets:

```bash
noah add me@some_host:path/to/my_dataset ftp://ftp.example.com/another_dataset # You can add multiple datasets at once
```

To share your project with others, simply push it to GitHub, and they can retrieve the data with the `noah install` command:

```bash
git clone https://github.com/me/my_project.git
cd my_project
noah install
```

For more information, please refer to [examples](examples/README.md).

# License

Noah is licensed under the MIT license. See [LICENSE](LICENSE) for details.
