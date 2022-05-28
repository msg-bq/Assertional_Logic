from experta import *
from itertools import chain
from Assertional_Logic.config import *

class DuplicateError(Exception):
    def __init__(self,ErrorInfo):
        super().__init__(self)
        self.errorinfo=ErrorInfo
    def __str__(self):
        return self.errorinfo

def create_individual_concept(class_name, parent_classes='Base', val_dict={}):
    '''
    :param class_name: 新类的名字
    :param parent_classes: 要继承的类，默认Base。否则应当输入需要继承的Concept的名字，如['INT', 'PERSON']
    :param val_dict: emm...我暂时没有用途，先留着。
    :return: individual和concept的类
    '''
    if class_name + 'Concept' in Declared_Concepts_Individuals:
        raise DuplicateError("此Concept已声明")

    individual_class = None
    concept_class = None
    if parent_classes == 'Base' or parent_classes == None:
        individual_class = type(class_name, (BaseIndividual,), {'name': class_name + 'Individual', **val_dict})
        concept_class = type(class_name, (BaseConcept,), {'name': class_name + 'Concept', **val_dict})
    else:
        parent_individual = tuple(Declared_Concepts_Individuals[name + 'Individual'] for name in parent_classes)
        parent_concept = tuple(Declared_Concepts_Individuals[name + 'Concept'] for name in parent_classes)

        individual_class = type(class_name, parent_individual, {'name': class_name + 'Individual', **val_dict})
        concept_class = type(class_name, parent_concept, {'name': class_name + 'Concept', **val_dict})

    Declared_Concepts_Individuals[class_name + 'Individual'] = individual_class
    Declared_Concepts_Individuals[class_name + 'Concept'] = concept_class

    return individual_class, concept_class

def check_scope(InputVariables, Scopes):
    '''
    为了简单起见，这个函数尽量只用于匹配concept角度是否正确，而不用于匹配具体individual的值是否一模一样。虽然确实提供了简单的匹配值的能力。
    复杂的值匹配靠schema处理吧，我尽量试着绕开重复造轮子的情况
    '''

    def check_single_input(InputVariable, Scope):
        if Scope == 'ANY' or type(InputVariable) == W:
            return True

        # if isinstance(InputVariable, Scope):
        #     return InputVariable==Scope
        # else:
        #     if isinstance(BaseIndividual, InputVariable) and
        if isinstance(InputVariable, BaseIndividual):
            if isinstance(Scope, BaseIndividual):
                return InputVariable == Scope
            else:
                match = Scope  # 这一行目前成无意义的了。BaseConcept正常匹配
                if Scope is Term:  # Scope非要用Term的情况，应该只有占位符。我们暂时取消了所有的占位符，所以我就不写这个了。留个提醒
                    print("碰到再说")
                    pass

                return Declared_Concepts_Individuals[InputVariable.name[:len(InputVariable.name) - len('Individual')] + 'Concept'] in match.mro()

        elif isinstance(InputVariable, BaseConcept):
            if Scope is BaseIndividual:
                return False

            match = Scope  # 这一行目前成无意义的了。 BaseConcept正常匹配
            if Scope is Term:  # Scope非要用Term的情况，应该只有占位符。我们暂时取消了所有的占位符，所以我就不写这个了。留个提醒
                print("碰到再说")
                pass

            return type(InputVariable) in type(match).mro()

        elif isinstance(InputVariable, Term):  # 我最近的建模中把占位符去掉了，这个情况理论上是会被规避掉的。只保留做个提醒，或许日后需要
            if Scope is BaseIndividual:
                return False

            match = Scope  # 这一行目前成无意义的了。BaseConcept正常匹配
            if Scope is Term:  # Scope非要用Term的情况，应该只有占位符。我们暂时取消了所有的占位符，所以我就不写这个了。留个提醒
                print("碰到再说")
                pass

            return InputVariable.operator.outputType in match.mro()

        elif isinstance(InputVariable, Assertion):
            print("碰到再说")  # 我还没实地见过
        else:
            return False

    if not isinstance(Scopes, list):
        InputVariables = [InputVariables]
        Scopes = [Scopes]

    assert len(InputVariables) == len(Scopes)

    for InputVariable, Scope in zip(InputVariables, Scopes):
        if isinstance(Scope, list):
            if sum([check_single_input(InputVariable, s) for s in Scope]) == 0:  # 有一个对了就行
                return False
        else:
            if not check_single_input(InputVariable, Scope):
                return False
    return True

class BaseIndividual(object):
    '''
    其实这个也可以被替换掉，因为我只要在BaseConcept class给一个叫self.value的属性，那么这个属性有值的时候，它就是一个individual。为空时表示整个concept
    这样就等价于目前的处理方法。这样只是能强化一下对AL的印象hhh，但是写得繁琐一点。这你们随缘叭，反正按道理怎么选都行。
    '''

    def __init__(self, value, comments='null', *args, **kwargs):
        self.value = value  # 值
        self.comments = comments  # 注释
        # self.name = name  # 个体的类型名，不过考虑到大概率不会从BaseIndividual实例化，而是从某个继承了Base的，比如PHIndividual上实例化
        # 所以这个那么也就不必输入了
        # self.update(self.GetUpdate(*args, **kwargs))

    def GetUpdate(self, *args, **kwargs):
        var_dict = self.__dict__
        var_dict.update(dict(chain(enumerate(args), kwargs.items())))

        return var_dict

    def update(self, mapping):
        for k, v in mapping.items():
            self[k] = v

    def __eq__(self, other):
        return type(self) is type(other) and self.GetHash() == other.GetHash()

    def GetHash(self):
        return (self.value, self.name)

    def __hash__(self):
        return self.GetHash().__hash__()

    def __getitem__(self, item):
        return self.__dict__[item]

class BaseConcept(object):

    def __init__(self, name, comments='null', *args, **kwargs):
        self.name = name  # 概念名/概念类型，反正我们不会没事儿实例化一个concept，只会继承或定义，所以这里要求那么倒也无妨（和BaseIndividual对比）
        self.comments = comments  # 注释
        # self.unary_ops = [] #一元算子，即私有属性
        self.update(self.GetUpdate(*args, **kwargs))

    def GetUpdate(self, *args, **kwargs):
        var_dict = self.__dict__
        var_dict.update(dict(chain(enumerate(args), kwargs.items())))

        return var_dict

    def update(self, mapping):
        for k, v in mapping.items():
            self[k] = v

    def __eq__(self, other):
        return type(self) is type(other) and self.GetHash() == other.GetHash()

    def GetHash(self):
        return self.name

    def __hash__(self):
        return self.GetHash().__hash__()


class BaseOperator(object):
    def __init__(self, name, variables_name, inputType=None, outputType=None, outputName=None, func=None,
                 comments='null', *args, **kwargs):
        if name in Declared_Operators:
            raise DuplicateError("此Operator已声明")
        Declared_Operators[name] = True

        self.variables_name = variables_name
        self.inputType = inputType
        assert len(self.variables_name) == len(self.inputType)
        self.outputType = outputType
        self.func = func
        self.outputName = outputName
        self.comments = comments
        self.name = name

    def GetUpdate(self, *args, **kwargs):
        var_dict = self.__dict__
        var_dict.update(dict(chain(enumerate(args), kwargs.items())))

        return var_dict

    def update(self, mapping):
        for k, v in mapping.items():
            self[k] = v

    def __call__(self, variables):
        '''
        这里就认为Individual是简单的tuple了
        '''
        if self.func == None:
            return None
        else:
            return self.func(*variables)

    def GetHash(self):
        return self.name  #因为名称唯一，按理来说这就够用了

    def __hash__(self):
        return self.GetHash().__hash__()

    def __eq__(self, other):
        return type(self) is type(other) and self.GetHash() == other.GetHash()


class Term(object):
    '''
    我们在这里约定，仅认为op(c1,c2...)是term，而不遵循常规的term定义。因为目前没啥必要，而且影响if语句的简洁
    '''

    def __init__(self, operator='null', variables='null', comments='', *args, **kwargs):
        self.operator = operator  # BaseOperator
        self.comments = comments
        self.variables = variables
        if not operator == 'null' and not operator == None:
            assert len(self.variables) == len(self.operator.variables_name)
            self.variables = list(self.variables)
            for pos, (variable, v_type) in enumerate(zip(self.variables, self.operator.inputType)):
                # 如果是用的python内置的数值类型，而不是concept，则自动转化
                if type(variable) in [str, int, float, list, tuple, dict]:
                    class_name = v_type.name[:len(v_type.name) - len('Concept')] + 'Individual'
                    individual_var = Declared_Concepts_Individuals[class_name](variable, class_name)
                    # 默认InputType都用的是concept而不是individual
                    self.variables[pos] = individual_var

            for variable, v_type in zip(self.variables, self.operator.inputType):
                if not check_scope(variable, v_type):
                    assert 1 == 0

            self.variables = tuple(self.variables)


    def GetUpdate(self, *args, **kwargs):
        var_dict = self.__dict__
        var_dict.update(dict(chain(enumerate(args), kwargs.items())))

        return var_dict

    def update(self, mapping):
        for k, v in mapping.items():
            self[k] = v

    def GetFinalVariables(self, variables):
        new_variable = []
        for variable in variables:
            if isinstance(variable, Term):  # 先不考虑assertion
                tmp = variable.operator(self.GetFinalVariables(variable.variables))
                if isinstance(tmp, list):
                    new_variable.extend(tmp)
                else:
                    new_variable.append(tmp)
            else:
                new_variable.append(variable)
        return tuple(new_variable)

    def GetRHS(self):
        RHS = self.operator(self.GetFinalVariables(self.variables))
        if type(RHS) in [str, int, float, list, tuple, dict]:
            v_type = self.operator.outputType
            class_name = v_type.name[:len(v_type.name) - len('Concept')] + 'Individual'
            RHS = Declared_Concepts_Individuals[class_name](RHS, class_name)

        return RHS  # 返回None的时候代表着不可执行，有可能会用到这个判断

    def GetHash(self):
        var_dict = {}
        for var, var_name in zip(self.variables, self.operator.variables_name):
            var_dict[var_name] = var.GetHash()
            var_dict['operator'] = self.operator.GetHash()
        return Fact(**var_dict)

    def __getattribute__(self, item):
        return super(Term, self).__getattribute__(item)

    def __hash__(self):
        return self.GetHash().__hash__()

    def __eq__(self, other):
        return type(self) is type(other) and self.GetHash() == other.GetHash()

    def __getitem__(self, item):
        return self.__dict__[item]

class Assertion(Fact):
    def __init__(self, LHS='null', RHS='null', comments='null', *args, **kwargs):
        super(Fact).__init__()
        self.LHS = LHS
        self.RHS = RHS

        if not self.LHS == 'null' and not isinstance(self.LHS, W):  # 不排除第二个判断在其他地方有遗漏
            assert isinstance(self.LHS, Term) or isinstance(self.LHS, W)  # 这个约束也是非常规的，不过...别的形式目前也没啥用
        if not self.RHS == 'null' and not isinstance(self.RHS, W):
            assert not self.LHS == 'null' and not isinstance(self.LHS, W)  # 给了这个约束是在于，就算是W()，那一个不提供operator的Assertion也是没意义的
            # 我充其量询问，我啥时候在上海读得书啊？，上海是RHS。但不可能问，我的哪些信息是和上海有关的（或者说我的哪些算子的RHS是上海，这个通常没有意义）
            # 当然了，这个要求是可以随着需求放宽的

            # 如果是用的python内置的数值类型，而不是concept，则自动转化
            if not isinstance(self.RHS, BaseIndividual):
                v_type = self.LHS.operator.outputType
                class_name = v_type.name[:len(v_type.name) - len('Concept')] + 'Individual'
                individual_var = Declared_Concepts_Individuals[class_name](self.RHS, class_name)
                # 默认InputType都用的是concept而不是individual
                self.RHS = individual_var

            assert check_scope(self.RHS, LHS.operator.outputType)  # in type().mro()
            assert isinstance(self.RHS, BaseConcept) or isinstance(self.RHS, BaseIndividual) or isinstance(self.RHS, Term)

        self.comments = comments
        self.update(self.GetUpdate(*args, **kwargs))

    def GetRHS(self):
        if self.RHS == 'null':
            return self.LHS.GetRHS()
        else:
            return self.RHS

    def GetUpdate(self, *args, **kwargs):
        var_dict = {}
        var_dict.update(dict(chain(enumerate(args), kwargs.items())))
        var_dict.update(self.__dict__)
        if self.LHS == 'null':
            del var_dict['LHS']
        if self.RHS == 'null':
            del var_dict['RHS']
        var_dict['comments'] = self.comments
        self.var_dict = var_dict
        return var_dict

    def __getattribute__(self, attr):
        if attr in self:
            self.__setattr__(attr, self[attr])
        return super(Assertion, self).__getattribute__(attr)

    def GetHash(self):
        # return Fact(**self.var_dict)
        var_dict = {k:v for k, v in self.items() if not k.startswith('__')}
        if self.LHS != 'null' and not isinstance(self.LHS, W):
            var_dict['LHS'] = self.LHS.GetHash()
        else:
            var_dict['LHS'] = self.LHS

        if self.RHS != 'null' and not isinstance(self.RHS, W):
            var_dict['RHS'] = self.RHS.GetHash()
        else:
            var_dict['RHS'] = self.RHS

        # so，根据目前的匹配机制，Assertion(4 = Term(2+2))与 Assertion(4 = 4)并不认为是一样的。同样的，有需要的话这里是可以放宽的。
        return Fact(**var_dict)

    def __eq__(self, other):
        return type(self) is type(other) and self.GetHash() == other.GetHash()

    def __hash__(self):
        return self.GetHash().__hash__()

    def __repr__(self):
        # for key in self.var_dict:
        #     if hasattr(self.var_dict[key], 'GetHash'):
        #         self.var_dict[key] = self.var_dict[key].GetHash()
        return str(self.GetHash())

    def __str__(self):
        return self.__repr__()

class Question(Fact):
    pass