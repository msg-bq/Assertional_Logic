from experta import *
from Assertional_Logic import *
from itertools import chain

class Round(Fact):
    pass

class DamageDeal(Fact):
    pass

Damage_dict = {'Thunderbolt': 90,
               'Rest': -200,
               'Body Slam': 100} #简单起见，正数是扣血，负数是治疗

Chinese_name = {'Thunderbolt': '十万伏特',
                'Rest': '睡觉',
                'Body Slam': '泰山压顶',
                'Pikachu': '皮卡丘',
                'Snorlax': '卡比兽'}

PokemonIndividual, PokemonConcept = create_individual_concept('Pokemon', 'Base')
PHIndividual, PHConcept = create_individual_concept('PH', 'Base')
MOVEIndividual, MOVEConcept = create_individual_concept('MOVE', 'Base') #招式

DamageDealingOperator = BaseOperator(name='DamageDealingOperator',
                                     variables_name=['PokemonPH', 'MOVE'],
                                     inputType=[PHConcept, MOVEConcept], #对比这两个输入，第一条输入可选项是Pokemon自身或PH(数值)，
                                     # 第二个输入可以是MOVE或Damage(数值)。我选了两种不同的风格，就是说有全局变量或可计算的，可以直接给
                                     #物体本身(MOVE)，如果是用断言表示的，且我们没构建快速搜索的字典的话，那么把数值带进来是个不错的选择。
                                     outputType=PHConcept,
                                     outputName='RemainingPH',
                                     func=lambda x, y: max(0, x.value - Damage_dict[y.value]))
#这里做了简化，伤害/治疗均称为伤害，并且伤害只有固伤、仅针对敌方；治疗也是固定值，仅针对自己。同时不考虑血条上限

PHOperator = BaseOperator(name='PHOperator',
                          variables_name=['Pokemon'],
                          inputType=[PokemonConcept],
                          outputType=PHConcept,
                          outputName='PH',
                          func=None)

Q1 = Assertion(LHS__operator=PHOperator,
               LHS__variables__0__value=MATCH.Q_pokemon,
               RHS__value=MATCH.Q_hp)

QUESTION_DICT['Q1'] = {}
Q2 = Question(name='Q1')

class Pikachu_VS_Snorlax_System(KnowledgeEngine): #Snorlax卡比兽
    '''
    这个显然不算是正经推理，不过它可以和正经推理一样地展示使用方法，我觉得还是够了的~
    规则是：
    1. 在皮卡丘的回合，它一定会使用十万伏特
    2. 在卡比兽的回合，<=100血会使用睡觉
    3. 在卡比兽的回合，>100血会使用泰山压顶
    4/5. 一方血量为0将结束对战，默认不出现同0的情况，此规则被重复实现，用于表示不同的使用方法
    （招式，包括睡觉，都是当回合结算）
    6. 当对局完全结束后，输出仍在场上的神奇宝贝及对应血量，使用提问(class Question)获取。
    即此规则等价于如何查询"最后还在场上的宝可梦是谁？血量多少？"
    '''

    def update_round(self, round):
        if round['Pokemon'] == round['Participates'][0]:
            self.modify(self.facts[round.__factid__], Pokemon=round['Participates'][1])
        else:
            self.modify(self.facts[round.__factid__], Round= round['Round']+1, Pokemon=round['Participates'][0])

    def terminate_round(self, round):
        self.retract(round)
        print("回合结束")

    @DefFacts()
    def SetDefault(self):
        yield Assertion(LHS=Term(operator=PHOperator,
                                 variables=['Pikachu']),
                        RHS=100)
        yield Assertion(LHS=Term(operator=PHOperator,
                                 variables=['Snorlax']),
                        RHS=100)

    @Rule(AS.round << Round(Round=W(), Pokemon='Pikachu'),
          AS.snorlax << Assertion(LHS=Term(operator=PHOperator,
                                           variables=['Snorlax']),
                                  RHS=W()),
          AS.pikaqiu << Assertion(LHS=Term(operator=PHOperator,
                                           variables=['Pikachu']),
                                  RHS=W()),
          salience=0) #规则1
    #另外注意一点，如果规则4使用了salience，那么规则1也必须给出salience，原因可能是：同时被触发的规则需要同时给出salience。理论上默认是0的样子
    def rule1(self, round, snorlax, pikaqiu):
        print("第{Round}轮，{Pokemon}出招".format(**round))
        Move = 'Thunderbolt'
        print("Pikachu对Snorlax使用{}".format(Move))
        PH_last = snorlax.GetRHS()
        PH_new = Term(operator=DamageDealingOperator,
                      variables=(snorlax.RHS, Move)).GetRHS()
        print("Snorlax受到了攻击！PH从{}降到了{}".format(PH_last.value, PH_new.value))
        print("--------------------")
        self.modify(self.facts[snorlax.__factid__], RHS=PH_new)
        self.update_round(round)

    @Rule(AS.round << Round(Round=W(), Pokemon='Snorlax'),
          AS.snorlax << Assertion(LHS=Term(operator=PHOperator,
                                           variables=['Snorlax']),
                                  RHS=W()),
          AS.pikaqiu << Assertion(LHS=Term(operator=PHOperator,
                                           variables=['Pikachu']),
                                  RHS=W()),
          TEST(lambda snorlax: snorlax.GetRHS().value <= 100),
          salience=0) #规则2
    def rule2(self, round, snorlax, pikaqiu):
        print("第{Round}轮，{Pokemon}出招".format(**round))
        Move = 'Rest'
        print("Snorlax对自己使用{}".format(Move))
        PH_last = snorlax.GetRHS()
        PH_new = Term(operator=DamageDealingOperator,
                      variables=(snorlax.RHS, Move)).GetRHS()
        print("Snorlax恢复了精力！PH从{}升到了{}".format(PH_last.value, PH_new.value))
        print("--------------------")
        self.modify(self.facts[snorlax.__factid__], RHS=PH_new)
        self.update_round(round)

    @Rule(AS.round << Round(Round=W(), Pokemon='Snorlax'),
          AS.snorlax << Assertion(LHS=Term(operator=PHOperator,
                                           variables=['Snorlax']),
                                  RHS=W()),
          AS.pikaqiu << Assertion(LHS=Term(operator=PHOperator,
                                           variables=['Pikachu']),
                                  RHS=W()),
          TEST(lambda snorlax: snorlax.GetRHS().value > 100),
          salience=0)  # 规则3
    def rule3(self, round, snorlax, pikaqiu):
        print("第{Round}轮，{Pokemon}出招".format(**round))
        Move = 'Body Slam'
        print("Snorlax对Pikachu使用{}".format(Move))
        PH_last = pikaqiu.GetRHS()
        PH_new = Term(operator=DamageDealingOperator,
                      variables=(pikaqiu.RHS, Move)).GetRHS()
        print("Pikachu受到了攻击！PH从{}降到了{}".format(PH_last.value, PH_new.value))
        print("--------------------")
        self.modify(self.facts[pikaqiu.__factid__], RHS=PH_new)
        self.update_round(round)

    @Rule(AS.round << Round(Round=W(), Pokemon=W()),
          AS.final << Assertion(LHS=W(),
                                RHS=W()),
          TEST(lambda final: final.LHS.operator==PHOperator and final.RHS.value==0
               if isinstance(final, Assertion) else False),
          salience=0.7) #规则4
    def rule4(self, round, final):
        Participates = list(round['Participates'])
        Participates.remove(round['Pokemon'])
        opposite = Participates[0]
        print("{}失去战斗能力，{}获胜!".format(round['Pokemon'], opposite))

        self.terminate_round(round)
        print("--------------------")

    @Rule(AS.round << Round(Round=W(), Pokemon=W()),
          AS.final << Assertion(LHS__operator=PHOperator,
                                RHS__value=0),
          salience=0.9)#其实就是rule4，我就是展示一下嵌套匹配。我让这个的salience高于上一条@Rule了，执行它那就说明等价
    def rule5(self, round, final):
        print("嵌套匹配√")
        Participates = list(round['Participates'])
        Participates.remove(round['Pokemon'])
        opposite = Participates[0]
        print("{}失去战斗能力，{}获胜!".format(round['Pokemon'], opposite))

        self.terminate_round(round)
        print("--------------------")

    @Rule(NOT(Round()),
          Assertion(**Q1),
          TEST(lambda Q_hp: Q_hp is not None and Q_hp > 0),
          salience=0.7)
    def rule6(self, *args, **kwargs):
        match_vars = dict(chain(enumerate(args), kwargs.items()))
        questions = {k[2:]: v for k, v in match_vars.items() if k.startswith('Q_')}
        print("最后在场的宝可梦是{pokemon}，剩余HP为{hp}".format(**questions))
        print("--------------------")

    @Rule(NOT(Round()),
          AS.Question << Q2,
          TEST(lambda Q_hp: Q_hp is not None and Q_hp > 0),
          salience=1)
    def rule7(self, Question, *args, **kwargs):
        print("rule7生效")
        match_vars = dict(chain(enumerate(args), kwargs.items()))
        questions = {k[2:]:v for k, v in match_vars.items() if k.startswith('Q_')}
        print("最后在场的宝可梦是{pokemon}，剩余HP为{hp}".format(**questions))
        self.retract(Question) #可正常执行，Question捕获正常
        print("--------------------")

QUESTION_DICT['Q1'] = Q1

engine = Pikachu_VS_Snorlax_System()
engine.reset()
engine.declare(Round(Round=1, Pokemon='Pikachu', Participates=('Pikachu', 'Snorlax')))
engine.run()