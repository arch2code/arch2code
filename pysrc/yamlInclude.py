#!/usr/bin/env python3
#https://github.com/marsoloGit/ccorp_yaml_include
#MIT License
#Author: Marina Lalazarova
#Author-email: marsolo@mail.ru
import types
import os

import ruamel.yaml
import ruamel.yaml.composer
import ruamel.yaml.constructor
from ruamel.yaml.nodes import ScalarNode, MappingNode, SequenceNode


class CompositingComposer(ruamel.yaml.composer.Composer):
    compositors = { k: {} for k in (ScalarNode, MappingNode, SequenceNode)}

    @classmethod
    def add_compositor(cls, tag, compositor, *, nodeTypes=(ScalarNode,)):
        for nodeType in nodeTypes:
            cls.compositors[nodeType][tag] = compositor

    @classmethod
    def get_compositor(cls, tag, nodeType):
        return cls.compositors[nodeType].get(tag, None)

    def __compose_dispatch(self, anchor, nodeType, callback):
        event = self.parser.peek_event()
        compositor = self.get_compositor(event.tag, nodeType) or callback
        if isinstance(compositor, types.MethodType):
            return compositor(anchor)
        else:
            return compositor(self, anchor)

    def compose_scalar_node(self, anchor):
        return self.__compose_dispatch(anchor, ScalarNode, super().compose_scalar_node)
    
    def compose_sequence_node(self, anchor):
        return self.__compose_dispatch(anchor, SequenceNode, super().compose_sequence_node)
    
    def compose_mapping_node(self, anchor):
        return self.__compose_dispatch(anchor, MappingNode, super().compose_mapping_node)


class ExcludingConstructor(ruamel.yaml.constructor.Constructor):
    filters = { k: [] for k in (MappingNode, SequenceNode)}

    @classmethod
    def add_filter(cls, filter, *, nodeTypes=(MappingNode,)):
        for nodeType in nodeTypes:
            cls.filters[nodeType].append(filter)

    def construct_mapping(self, node):
        node.value = [(key_node, value_node) for key_node, value_node in node.value
                if not any(f(key_node, value_node) for f in self.filters[MappingNode])]
        return super().construct_mapping(node)
    
    def construct_sequence(self, node, deep=True):
        node.value = [value_node for value_node in node.value if not any(f(value_node) for f in self.filters[SequenceNode])]
        return super().construct_sequence(node)


class YAML(ruamel.yaml.YAML):
    hiddenIncludes = list()
    def __init__(self, *args, **kwargs):
        if 'typ' not in kwargs:
            kwargs['typ'] = 'safe'
        elif kwargs['typ'] not in ('safe', 'unsafe') and kwargs['typ'] not in (['safe'], ['unsafe']):
            raise Exception("Can't do typ={} parsing w/ composition time directives!".format(kwargs['typ']))
        
        if 'pure' not in kwargs:
            kwargs['pure'] = True
        elif not kwargs['pure']:
            raise Exception("Can't do non-pure python parsing w/ composition time directives!")

        super().__init__(*args, **kwargs)
        self.Composer = CompositingComposer
        self.Constructor = ExcludingConstructor

    def compose(self, stream):
        # type: (Union[Path, StreamTextType]) -> Any
        """
        at this point you either have the non-pure Parser (which has its own reader and
        scanner) or you have the pure Parser.
        If the pure Parser is set, then set the Reader and Scanner, if not already set.
        If either the Scanner or Reader are set, you cannot use the non-pure Parser,
            so reset it to the pure parser and set the Reader resp. Scanner if necessary
        """
        constructor, parser = self.get_constructor_parser(stream)
        try:
            return self.composer.get_single_node()
        finally:
            parser.dispose()
            try:
                self._reader.reset_reader()
            except AttributeError:
                pass
            try:
                self._scanner.reset_scanner()
            except AttributeError:
                pass

    def fork(self):
        yaml = type(self)(typ=self.typ, pure=self.pure)
        yaml.composer.anchors = self.composer.anchors
        return yaml


def include_compositor(self, anchor):
    event = self.parser.get_event()
    yaml = self.loader.fork()
    path = os.path.join(os.path.dirname(self.loader.reader.name), event.value)
    YAML.hiddenInclude.append(os.path.relpath(path))
    with open(os.path.abspath(path)) as f:
        return yaml.compose(f)


def exclude_filter(key_node, value_node = None):
    value_node = value_node or key_node # copy ref if None
    return key_node.tag == '!exclude' or value_node.tag == '!exclude'


CompositingComposer.add_compositor('!include', include_compositor) 
ExcludingConstructor.add_filter(exclude_filter, nodeTypes=(MappingNode, SequenceNode))


if __name__ == '__main__':
    import argparse
    import pprint

    yaml = YAML(typ='safe', pure=True)
    parser = argparse.ArgumentParser()
    parser.add_argument('file')

    args = parser.parse_args()

    with open(args.file) as f:
        pprint.pprint(yaml.load(f))
