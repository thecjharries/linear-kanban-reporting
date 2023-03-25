#!/usr/bin/env bash

jupyter contrib nbextension install --sys-prefix
jupyter nbextensions_configurator enable --sys-prefix
jupyter nbextension enable widgetsnbextension --py --sys-prefix
jupyter nbextension enable python-markdown/main --sys-prefix
