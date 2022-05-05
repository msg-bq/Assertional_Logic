# Assertional_Logic
 提供了支持断言逻辑的推理引擎实现。
 推理引擎使用experta作为基础，其对应的document见[此处](https://experta.readthedocs.io/en/latest/thebasics.html)

 包括Individual, Concept, Operator, Term, Assertion，其中Term约定为仅包括op(C1, C2...)的形式

 样例中给出了使用方法(在examples文件夹内有[完整代码文件](/examples/Pokemon.py)，大家也可以再补几个例子)，
 下面是精简版：
 ```python
Chinese_name = {'Thunderbolt': '十万伏特',
                'Rest': '睡觉',
                'Body Slam': '泰山压顶',
                'Pikachu': '皮卡丘',
                'Snorlax': '卡比兽'}

PokemonIndividual, PokemonConcept = create_individual_concept('Pokemon', 'Base')
#还有PH, MOVE(招式)

DamageDealingOperator = BaseOperator(name='DamageDealingOperator',
                                     variables_name=['PokemonPH', 'MOVE'],
                                     inputType=[PHConcept, MOVEConcept], 
                                     outputType=PHConcept,
                                     outputName='RemainingPH',
                                     func=lambda x, y: max(0, x.value - Damage_dict[y.value]))
#这里做了简化，伤害/治疗均称为伤害，并且伤害只有固伤、仅针对敌方；治疗也是固定值，仅针对自己。同时不考虑血条上限
#还有PH算子，输入Pokemon输出PH

class Pikachu_VS_Snorlax_System(KnowledgeEngine): #Snorlax卡比兽
    '''
    这个显然不算是正经推理，不过它可以和正经推理一样地展示使用方法，我觉得还是够了的~
    规则是：
    1. 在皮卡丘的回合，它一定会使用十万伏特
    2. 在卡比兽的回合，<=100血会使用睡觉
    3. 在卡比兽的回合，>100血会使用泰山压顶
    4. 一方血量为0将结束对战，默认不出现同0的情况
    （招式，包括睡觉，都是当回合结算）
    '''
    @DefFacts()
    def SetDefault(self):
        pass #初始血量各100

    @Rule(AS.round << Round(Round=W(), Pokemon='Pikachu'), salience=0) #规则1
    def rule1(self, round, snorlax, pikaqiu):
        pass

    @Rule(AS.round << Round(Round=W(), Pokemon='Snorlax'),
          TEST(lambda snorlax: snorlax.GetRHS().value <= 100),
          salience=0) #规则2
    @Rule(TEST(lambda snorlax: snorlax.GetRHS().value > 100), salience=0)# 规则3
    @Rule(TEST(lambda final: final.LHS.operator==PHOperator and final.RHS.value==0), 
          salience=1) #规则4

engine = Pikachu_VS_Snorlax_System()
engine.reset()
engine.declare(Round(Round=1, Pokemon='Pikachu', Participates=('Pikachu', 'Snorlax')))
engine.run()

#---------Output-----------
#第1轮，Pikachu出招
#Pikachu对Snorlax使用Thunderbolt
#Snorlax受到了攻击！PH从100降到了10
#--------------------
#第1轮，Snorlax出招
#Snorlax对自己使用Rest
#Snorlax恢复了精力！PH从10升到了210
#--------------------
#第2轮，Pikachu出招
#Pikachu对Snorlax使用Thunderbolt
#Snorlax受到了攻击！PH从210降到了120
#--------------------
#第2轮，Snorlax出招
#Snorlax对Pikachu使用Body Slam
#Pikachu受到了攻击！PH从100降到了0
#--------------------
#Pikachu失去战斗能力，Snorlax获胜!
#回合结束
#--------------------
 ```

**TODO**:
- [ ] 支持对断言相关类的嵌套匹配(其他的嵌套匹配不影响，具体使用查看experta的document)，目前嵌套匹配的需求需要自己写一两行TEST来实现。
继承dict类会有奇怪的bug，所以暂时不支持。
- [ ] 待支持&, |, ~, 这个暂时手动TEST一下吧，直接用python的&, |, 和not即可代替。
- [ ] 待支持L()和P()，因为L是默认调用，无所谓是否显式地支持。然后P()应该只是TEST的简略写法，而TEST是可以正常使用的。
- [ ] 未知...