#!/usr/bin/env python3
"""LR(0) parser with automatic table generation."""
import sys
from collections import defaultdict

class Item:
    def __init__(self, lhs, rhs, dot=0):
        self.lhs, self.rhs, self.dot = lhs, tuple(rhs), dot
    def completed(self): return self.dot >= len(self.rhs)
    def next_sym(self): return self.rhs[self.dot] if not self.completed() else None
    def advance(self): return Item(self.lhs, self.rhs, self.dot + 1)
    def __eq__(self, o): return self.lhs == o.lhs and self.rhs == o.rhs and self.dot == o.dot
    def __hash__(self): return hash((self.lhs, self.rhs, self.dot))
    def __repr__(self): return f"{self.lhs} -> {' '.join(self.rhs[:self.dot])} . {' '.join(self.rhs[self.dot:])}"

def closure(items, grammar):
    result = set(items)
    changed = True
    while changed:
        changed = False
        for item in list(result):
            s = item.next_sym()
            if s and s in grammar:
                for rhs in grammar[s]:
                    new = Item(s, rhs, 0)
                    if new not in result:
                        result.add(new); changed = True
    return frozenset(result)

def goto(items, sym, grammar):
    moved = set()
    for item in items:
        if item.next_sym() == sym:
            moved.add(item.advance())
    return closure(moved, grammar) if moved else frozenset()

def build_table(grammar, start):
    aug_start = start + "'"
    aug_grammar = dict(grammar)
    aug_grammar[aug_start] = [[start]]
    init = closure({Item(aug_start, [start], 0)}, aug_grammar)
    states = [init]
    state_map = {init: 0}
    action = defaultdict(dict)
    goto_table = defaultdict(dict)
    i = 0
    while i < len(states):
        state = states[i]
        syms = {item.next_sym() for item in state if not item.completed()} - {None}
        for sym in syms:
            target = goto(state, sym, aug_grammar)
            if target:
                if target not in state_map:
                    state_map[target] = len(states)
                    states.append(target)
                j = state_map[target]
                if sym[0].isupper():
                    goto_table[i][sym] = j
                else:
                    action[i][sym] = ('shift', j)
        for item in state:
            if item.completed():
                if item.lhs == aug_start:
                    action[i]['$'] = ('accept',)
                else:
                    for t in list(action[i].keys()) + ['$'] + [s for s in syms if not s[0].isupper()]:
                        if t not in action[i]:
                            action[i][t] = ('reduce', item.lhs, item.rhs)
                    # Simple: reduce on all terminals
                    all_terms = set()
                    for s in states:
                        for it in s:
                            ns = it.next_sym()
                            if ns and not ns[0].isupper(): all_terms.add(ns)
                    all_terms.add('$')
                    for t in all_terms:
                        if t not in action[i]:
                            action[i][t] = ('reduce', item.lhs, item.rhs)
        i += 1
    return action, goto_table

def lr_parse(action, goto_table, tokens):
    tokens = list(tokens) + ['$']
    stack = [0]
    pos = 0
    while True:
        state = stack[-1]
        tok = tokens[pos]
        if tok not in action[state]:
            return False
        act = action[state][tok]
        if act[0] == 'shift':
            stack.append(tok)
            stack.append(act[1])
            pos += 1
        elif act[0] == 'reduce':
            _, lhs, rhs = act
            for _ in range(len(rhs) * 2): stack.pop()
            state = stack[-1]
            stack.append(lhs)
            stack.append(goto_table[state][lhs])
        elif act[0] == 'accept':
            return True

def main():
    # E -> E + T | T, T -> n
    grammar = {'E': [['E', '+', 'T'], ['T']], 'T': [['n']]}
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        action, goto_t = build_table(grammar, 'E')
        assert lr_parse(action, goto_t, ['n', '+', 'n'])
        assert lr_parse(action, goto_t, ['n'])
        assert lr_parse(action, goto_t, ['n', '+', 'n', '+', 'n'])
        print("All tests passed!")
    else:
        action, goto_t = build_table(grammar, 'E')
        expr = sys.argv[1:] if len(sys.argv) > 1 else ['n', '+', 'n']
        print(f"LR parse '{' '.join(expr)}': {lr_parse(action, goto_t, expr)}")

if __name__ == "__main__":
    main()
