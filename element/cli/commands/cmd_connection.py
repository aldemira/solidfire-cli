#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright &copy; 2014-2016 NetApp, Inc. All Rights Reserved.

import click

import os
import csv
from element.cli.cli import pass_context
from pkg_resources import Requirement, resource_filename
import simplejson
from element.cli import utils as cli_utils
from solidfire.factory import ElementFactory

@click.group()
@pass_context
def cli(ctx):
    """Connection management"""

@cli.command('push', short_help="Pushes the connection onto connection.csv to save for later use.")
@pass_context
def push(ctx):
    # First, attempt to establish the connection. If that's not possible,
    # throw the error.
    try:
        ctx.element = ElementFactory.create(ctx.cfg["mvip"],ctx.cfg["username"],ctx.cfg["password"],ctx.cfg["version"],port=ctx.cfg["port"])
    except Exception as e:
        ctx.logger.error(e.__str__())
    if(ctx.cfg.get("name", "") is None):
        ctx.logger.error("Please provide a connection name.")
    connections = cli_utils.get_connections()
    if(ctx.cfg["username"] is not None and ctx.cfg["password"] is not None):
        ctx.cfg["username"] = cli_utils.encrypt(ctx.cfg["username"])
        ctx.cfg["password"] = cli_utils.encrypt(ctx.cfg["password"])
    connections = connections + [ctx.cfg]
    cli_utils.write_connections(connections)

@cli.command('remove', short_help="Removes a given connection")
@click.option('--name', '-n',
              type=str,
              required=False,
              help="""The name of the connection you wish to remove.""")
@click.option('--index', '-i',
              type=int,
              required=False,
              help="""The index of the connection you wish to remove - 0 is the oldest, 1 is the second oldest, and -1 is the newest.""")
@pass_context
def remove(ctx, name=None, index=None):
    if name is not None and index is not None:
        ctx.logger.error("You must provide either the name or the index. Not both.")
        exit(1)
    if name is None and index is None:
        ctx.logger.error("You must provide either the name or the index of the connection to remove.")
        exit(1)

    connections = cli_utils.get_connections()
    if index is not None and index > (len(connections) - 1):
        ctx.logger.error("Your connection index is greater than the maximum index of your connections stack.")

    # Filter by name
    if name is not None:
        connections = [connection for connection in connections if connection["name"]!=name]
    # Filter by index
    if index is not None:
        del connections[index]
    cli_utils.write_connections(connections)

@cli.command('list', short_help="Lists the stored connection info")
@click.option('--name', '-n',
              type=str,
              required=False,
              help="""The name of the connection you wish to view.""")
@click.option('--index', '-i',
              type=int,
              required=False,
              help="""The index of the connection you wish to view - 0 is the oldest, 1 is the second oldest, and -1 is the newest.""")
@pass_context
def list(ctx, name=None, index=None):
    connectionsCsvLocation = resource_filename(Requirement.parse("solidfire-cli"), "connections.csv")
    connections = cli_utils.get_connections()
    print(connectionsCsvLocation)
    if(name is None and index is None):
        cli_utils.print_result(connections, ctx.logger, as_json=ctx.json, as_pickle=ctx.pickle, depth=ctx.depth, filter_tree=ctx.filter_tree)
    if(name is None and index is not None):
        cli_utils.print_result(connections[int(index)], ctx.logger, as_json=ctx.json, as_pickle=ctx.pickle, depth=ctx.depth, filter_tree=ctx.filter_tree)
    if(name is not None and index is None):
        connections = [connection for connection in connections if connection["name"]==name]
        cli_utils.print_result(connections, ctx.logger, as_json=ctx.json, as_pickle=ctx.pickle, depth=ctx.depth, filter_tree=ctx.filter_tree)

@cli.command('prune', short_help="If something changes in your cluster, a connection which may have been valid before may not be valid now. To find and remove those connections, use prune.")
@pass_context
def prune(ctx):
    connections = cli_utils.get_connections()
    goodConnections = []
    for connection in connections:
        if not all (k in connection.keys() for k in ["mvip", "username", "password", "version", "port", "name"]):
            print("Removing connection, ")
            cli_utils.print_result(connection, ctx.logger, as_json=ctx.json, as_pickle=ctx.pickle, depth=ctx.depth, filter_tree=ctx.filter_tree)
            print("Connection info did not contain the following fields: mvip, username, password, version, port, and url")
            print()
            continue
        try:
            ElementFactory.create(connection["mvip"],cli_utils.decrypt(connection["username"]),cli_utils.decrypt(connection["password"]),version=connection["version"],port=connection["port"])
            goodConnections += [connection]
        except Exception as e:
            print("Removing connection, ")
            cli_utils.print_result(connection, ctx.logger, as_json=ctx.json, as_pickle=ctx.pickle, depth=ctx.depth, filter_tree=ctx.filter_tree)
            print(e.__str__())
            print()
    cli_utils.write_connections(goodConnections)