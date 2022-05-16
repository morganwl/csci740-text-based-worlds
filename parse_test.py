import test

parser = test.RoverLogicParser()

print(parser.parse('action_obj(go, D)'))
print(parser.parse('((+action_obj(go, D) & exit(location(p), D)) : at(p, destination(D)))'))
print(parser.parse(('((action_obj(go, D) & !(+at(p, location(p)) -> '
                    'connections(at(p), D, +at(p)))')))
