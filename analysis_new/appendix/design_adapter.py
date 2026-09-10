"""Reuse exact pure legacy design functions without their run-directory side effects.

Only the named function definitions and literal constants are read. No module
imports, top-level statements, fitting function or output-directory code execute.
The caller records and checks source hashes before this adapter is used.
"""
import ast
import numpy as np
import pandas as pd
from .catalog import ROOT

def load_design_functions(knots):
    context={'np':np,'pd':pd,'KN':knots}
    for source,names,constants in [
        ('analysis_new/model_selection.py',{'design'},{'SCALE','SOCIO'}),
        ('analysis_new/final_models.py',{'final_design'},set()),
    ]:
        tree=ast.parse((ROOT/source).read_text(encoding='utf-8-sig'))
        selected=[]
        for node in tree.body:
            if isinstance(node,ast.Assign):
                for target in node.targets:
                    if isinstance(target,ast.Name) and target.id in constants:
                        context[target.id]=ast.literal_eval(node.value)
            elif isinstance(node,ast.FunctionDef) and node.name in names:
                selected.append(node)
        if {n.name for n in selected}!=names: raise ValueError('Legacy pure design interface changed: '+source)
        module=ast.fix_missing_locations(ast.Module(body=selected,type_ignores=[]))
        exec(compile(module,str(ROOT/source),'exec'),context)
    return context['design'],context['final_design']
