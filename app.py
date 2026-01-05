"""
时间占卜工具 - 基于梅花易数时间起卦法
"""
import time
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from datetime import datetime, timezone, timedelta
from zhdate import ZhDate

# 定义中国标准时区 (UTC+8)
CHINA_TZ = timezone(timedelta(hours=8))

app = Flask(__name__)
CORS(app)

# 八卦基本信息
BAGUA = {
    1: {"name": "乾", "symbol": "☰", "nature": "天", "attribute": "刚健", "family": "父", "body": "首", "direction": "西北", "element": "金", "number": 1},
    2: {"name": "兑", "symbol": "☱", "nature": "泽", "attribute": "喜悦", "family": "少女", "body": "口", "direction": "西", "element": "金", "number": 2},
    3: {"name": "离", "symbol": "☲", "nature": "火", "attribute": "附丽", "family": "中女", "body": "目", "direction": "南", "element": "火", "number": 3},
    4: {"name": "震", "symbol": "☳", "nature": "雷", "attribute": "动", "family": "长男", "body": "足", "direction": "东", "element": "木", "number": 4},
    5: {"name": "巽", "symbol": "☴", "nature": "风", "attribute": "入", "family": "长女", "body": "股", "direction": "东南", "element": "木", "number": 5},
    6: {"name": "坎", "symbol": "☵", "nature": "水", "attribute": "陷", "family": "中男", "body": "耳", "direction": "北", "element": "水", "number": 6},
    7: {"name": "艮", "symbol": "☶", "nature": "山", "attribute": "止", "family": "少男", "body": "手", "direction": "东北", "element": "土", "number": 7},
    8: {"name": "坤", "symbol": "☷", "nature": "地", "attribute": "顺", "family": "母", "body": "腹", "direction": "西南", "element": "土", "number": 8},
}

# 六十四卦信息（含六爻爻辞）
HEXAGRAMS = {
    (1, 1): {
        "name": "乾为天", "judgement": "元亨利贞", "description": "天行健，君子以自强不息", "fortune": "大吉",
        "yaoci": {
            1: "初九：潜龙勿用",
            2: "九二：见龙在田，利见大人",
            3: "九三：君子终日乾乾，夕惕若厉，无咎",
            4: "九四：或跃在渊，无咎",
            5: "九五：飞龙在天，利见大人",
            6: "上九：亢龙有悔"
        }
    },
    (1, 2): {
        "name": "天泽履", "judgement": "履虎尾，不咥人，亨", "description": "上天下泽，履。君子以辨上下，定民志", "fortune": "吉",
        "yaoci": {
            1: "初九：素履往，无咎",
            2: "九二：履道坦坦，幽人贞吉",
            3: "六三：眇能视，跛能履，履虎尾，咥人，凶",
            4: "九四：履虎尾，愬愬终吉",
            5: "九五：夬履，贞厉",
            6: "上九：视履考祥，其旋元吉"
        }
    },
    (1, 3): {
        "name": "天火同人", "judgement": "同人于野，亨，利涉大川", "description": "天与火，同人。君子以类族辨物", "fortune": "吉",
        "yaoci": {
            1: "初九：同人于门，无咎",
            2: "六二：同人于宗，吝",
            3: "九三：伏戎于莽，升其高陵，三岁不兴",
            4: "九四：乘其墉，弗克攻，吉",
            5: "九五：同人，先号咷而后笑，大师克相遇",
            6: "上九：同人于郊，无悔"
        }
    },
    (1, 4): {
        "name": "天雷无妄", "judgement": "元亨利贞，其匪正有眚", "description": "天下雷行，物与无妄", "fortune": "中吉",
        "yaoci": {
            1: "初九：无妄，往吉",
            2: "六二：不耕获，不菑畬，则利有攸往",
            3: "六三：无妄之灾，或系之牛，行人之得，邑人之灾",
            4: "九四：可贞，无咎",
            5: "九五：无妄之疾，勿药有喜",
            6: "上九：无妄，行有眚，无攸利"
        }
    },
    (1, 5): {
        "name": "天风姤", "judgement": "姤，女壮，勿用取女", "description": "天下有风，姤。后以施命诰四方", "fortune": "中",
        "yaoci": {
            1: "初六：系于金柅，贞吉，有攸往，见凶",
            2: "九二：包有鱼，无咎，不利宾",
            3: "九三：臀无肤，其行次且，厉，无大咎",
            4: "九四：包无鱼，起凶",
            5: "九五：以杞包瓜，含章，有陨自天",
            6: "上九：姤其角，吝，无咎"
        }
    },
    (1, 6): {
        "name": "天水讼", "judgement": "讼，有孚窒惕，中吉，终凶", "description": "天与水违行，讼", "fortune": "凶",
        "yaoci": {
            1: "初六：不永所事，小有言，终吉",
            2: "九二：不克讼，归而逋，其邑人三百户，无眚",
            3: "六三：食旧德，贞厉，终吉，或从王事，无成",
            4: "九四：不克讼，复即命，渝安贞，吉",
            5: "九五：讼，元吉",
            6: "上九：或锡之鞶带，终朝三褫之"
        }
    },
    (1, 7): {
        "name": "天山遁", "judgement": "遁，亨，小利贞", "description": "天下有山，遁。君子以远小人", "fortune": "中",
        "yaoci": {
            1: "初六：遁尾，厉，勿用有攸往",
            2: "六二：执之用黄牛之革，莫之胜说",
            3: "九三：系遁，有疾厉，畜臣妾吉",
            4: "九四：好遁，君子吉，小人否",
            5: "九五：嘉遁，贞吉",
            6: "上九：肥遁，无不利"
        }
    },
    (1, 8): {
        "name": "天地否", "judgement": "否之匪人，不利君子贞", "description": "天地不交，否", "fortune": "凶",
        "yaoci": {
            1: "初六：拔茅茹，以其汇，贞吉亨",
            2: "六二：包承，小人吉，大人否亨",
            3: "六三：包羞",
            4: "九四：有命无咎，畴离祉",
            5: "九五：休否，大人吉，其亡其亡，系于苞桑",
            6: "上九：倾否，先否后喜"
        }
    },
    (2, 1): {
        "name": "泽天夬", "judgement": "夬，扬于王庭，孚号有厉", "description": "泽上于天，夬。君子以施禄及下", "fortune": "吉",
        "yaoci": {
            1: "初九：壮于前趾，往不胜为咎",
            2: "九二：惕号，莫夜有戎，勿恤",
            3: "九三：壮于頄，有凶，君子夬夬，独行遇雨",
            4: "九四：臀无肤，其行次且，牵羊悔亡，闻言不信",
            5: "九五：苋陆夬夬，中行无咎",
            6: "上六：无号，终有凶"
        }
    },
    (2, 2): {
        "name": "兑为泽", "judgement": "兑，亨，利贞", "description": "丽泽，兑。君子以朋友讲习", "fortune": "吉",
        "yaoci": {
            1: "初九：和兑，吉",
            2: "九二：孚兑，吉，悔亡",
            3: "六三：来兑，凶",
            4: "九四：商兑未宁，介疾有喜",
            5: "九五：孚于剥，有厉",
            6: "上六：引兑"
        }
    },
    (2, 3): {
        "name": "泽火革", "judgement": "革，巳日乃孚，元亨利贞", "description": "泽中有火，革。君子以治历明时", "fortune": "中吉",
        "yaoci": {
            1: "初九：巩用黄牛之革",
            2: "六二：巳日乃革之，征吉，无咎",
            3: "九三：征凶，贞厉，革言三就，有孚",
            4: "九四：悔亡，有孚改命，吉",
            5: "九五：大人虎变，未占有孚",
            6: "上六：君子豹变，小人革面，征凶，居贞吉"
        }
    },
    (2, 4): {
        "name": "泽雷随", "judgement": "随，元亨利贞，无咎", "description": "泽中有雷，随。君子以向晦入宴息", "fortune": "吉",
        "yaoci": {
            1: "初九：官有渝，贞吉，出门交有功",
            2: "六二：系小子，失丈夫",
            3: "六三：系丈夫，失小子，随有求得，利居贞",
            4: "九四：随有获，贞凶，有孚在道，以明，何咎",
            5: "九五：孚于嘉，吉",
            6: "上六：拘系之，乃从维之，王用亨于西山"
        }
    },
    (2, 5): {
        "name": "泽风大过", "judgement": "大过，栋桡，利有攸往", "description": "泽灭木，大过。君子以独立不惧", "fortune": "凶",
        "yaoci": {
            1: "初六：藉用白茅，无咎",
            2: "九二：枯杨生稊，老夫得其女妻，无不利",
            3: "九三：栋桡，凶",
            4: "九四：栋隆，吉，有它吝",
            5: "九五：枯杨生华，老妇得其士夫，无咎无誉",
            6: "上六：过涉灭顶，凶，无咎"
        }
    },
    (2, 6): {
        "name": "泽水困", "judgement": "困，亨，贞大人吉", "description": "泽无水，困。君子以致命遂志", "fortune": "凶",
        "yaoci": {
            1: "初六：臀困于株木，入于幽谷，三岁不觌",
            2: "九二：困于酒食，朱绂方来，利用亨祀，征凶，无咎",
            3: "六三：困于石，据于蒺藜，入于其宫，不见其妻，凶",
            4: "九四：来徐徐，困于金车，吝，有终",
            5: "九五：劓刖，困于赤绂，乃徐有说，利用祭祀",
            6: "上六：困于葛藟，于臲卼，曰动悔，有悔，征吉"
        }
    },
    (2, 7): {
        "name": "泽山咸", "judgement": "咸，亨，利贞，取女吉", "description": "山上有泽，咸。君子以虚受人", "fortune": "吉",
        "yaoci": {
            1: "初六：咸其拇",
            2: "六二：咸其腓，凶，居吉",
            3: "九三：咸其股，执其随，往吝",
            4: "九四：贞吉悔亡，憧憧往来，朋从尔思",
            5: "九五：咸其脢，无悔",
            6: "上六：咸其辅颊舌"
        }
    },
    (2, 8): {
        "name": "泽地萃", "judgement": "萃，亨，王假有庙", "description": "泽上于地，萃。君子以除戎器，戒不虞", "fortune": "中吉",
        "yaoci": {
            1: "初六：有孚不终，乃乱乃萃，若号一握为笑，勿恤，往无咎",
            2: "六二：引吉，无咎，孚乃利用禴",
            3: "六三：萃如嗟如，无攸利，往无咎，小吝",
            4: "九四：大吉，无咎",
            5: "九五：萃有位，无咎，匪孚，元永贞，悔亡",
            6: "上六：赍咨涕洟，无咎"
        }
    },
    (3, 1): {
        "name": "火天大有", "judgement": "大有，元亨", "description": "火在天上，大有。君子以遏恶扬善", "fortune": "大吉",
        "yaoci": {
            1: "初九：无交害，匪咎，艰则无咎",
            2: "九二：大车以载，有攸往，无咎",
            3: "九三：公用亨于天子，小人弗克",
            4: "九四：匪其彭，无咎",
            5: "六五：厥孚交如，威如，吉",
            6: "上九：自天祐之，吉无不利"
        }
    },
    (3, 2): {
        "name": "火泽睽", "judgement": "睽，小事吉", "description": "上火下泽，睽。君子以同而异", "fortune": "中",
        "yaoci": {
            1: "初九：悔亡，丧马勿逐，自复，见恶人无咎",
            2: "九二：遇主于巷，无咎",
            3: "六三：见舆曳，其牛掣，其人天且劓，无初有终",
            4: "九四：睽孤，遇元夫，交孚，厉无咎",
            5: "六五：悔亡，厥宗噬肤，往何咎",
            6: "上九：睽孤，见豕负涂，载鬼一车，先张之弧，后说之弧"
        }
    },
    (3, 3): {
        "name": "离为火", "judgement": "离，利贞，亨。畜牝牛吉", "description": "明两作，离。大人以继明照于四方", "fortune": "吉",
        "yaoci": {
            1: "初九：履错然，敬之无咎",
            2: "六二：黄离，元吉",
            3: "九三：日昃之离，不鼓缶而歌，则大耋之嗟，凶",
            4: "九四：突如其来如，焚如，死如，弃如",
            5: "六五：出涕沱若，戚嗟若，吉",
            6: "上九：王用出征，有嘉折首，获匪其丑，无咎"
        }
    },
    (3, 4): {
        "name": "火雷噬嗑", "judgement": "噬嗑，亨，利用狱", "description": "雷电，噬嗑。先王以明罚敕法", "fortune": "中吉",
        "yaoci": {
            1: "初九：屦校灭趾，无咎",
            2: "六二：噬肤灭鼻，无咎",
            3: "六三：噬腊肉，遇毒，小吝，无咎",
            4: "九四：噬乾胏，得金矢，利艰贞，吉",
            5: "六五：噬乾肉，得黄金，贞厉，无咎",
            6: "上九：何校灭耳，凶"
        }
    },
    (3, 5): {
        "name": "火风鼎", "judgement": "鼎，元吉，亨", "description": "木上有火，鼎。君子以正位凝命", "fortune": "大吉",
        "yaoci": {
            1: "初六：鼎颠趾，利出否，得妾以其子，无咎",
            2: "九二：鼎有实，我仇有疾，不我能即，吉",
            3: "九三：鼎耳革，其行塞，雉膏不食，方雨亏悔，终吉",
            4: "九四：鼎折足，覆公餗，其形渥，凶",
            5: "六五：鼎黄耳金铉，利贞",
            6: "上九：鼎玉铉，大吉，无不利"
        }
    },
    (3, 6): {
        "name": "火水未济", "judgement": "未济，亨，小狐汔济", "description": "火在水上，未济。君子以慎辨物居方", "fortune": "中",
        "yaoci": {
            1: "初六：濡其尾，吝",
            2: "九二：曳其轮，贞吉",
            3: "六三：未济，征凶，利涉大川",
            4: "九四：贞吉，悔亡，震用伐鬼方，三年有赏于大国",
            5: "六五：贞吉，无悔，君子之光，有孚，吉",
            6: "上九：有孚于饮酒，无咎，濡其首，有孚失是"
        }
    },
    (3, 7): {
        "name": "火山旅", "judgement": "旅，小亨，旅贞吉", "description": "山上有火，旅。君子以明慎用刑", "fortune": "中",
        "yaoci": {
            1: "初六：旅琐琐，斯其所取灾",
            2: "六二：旅即次，怀其资，得童仆贞",
            3: "九三：旅焚其次，丧其童仆，贞厉",
            4: "九四：旅于处，得其资斧，我心不快",
            5: "六五：射雉一矢亡，终以誉命",
            6: "上九：鸟焚其巢，旅人先笑后号咷，丧牛于易，凶"
        }
    },
    (3, 8): {
        "name": "火地晋", "judgement": "晋，康侯用锡马蕃庶", "description": "明出地上，晋。君子以自昭明德", "fortune": "吉",
        "yaoci": {
            1: "初六：晋如摧如，贞吉，罔孚，裕无咎",
            2: "六二：晋如愁如，贞吉，受兹介福，于其王母",
            3: "六三：众允，悔亡",
            4: "九四：晋如鼫鼠，贞厉",
            5: "六五：悔亡，失得勿恤，往吉无不利",
            6: "上九：晋其角，维用伐邑，厉吉无咎，贞吝"
        }
    },
    (4, 1): {
        "name": "雷天大壮", "judgement": "大壮，利贞", "description": "雷在天上，大壮。君子以非礼弗履", "fortune": "吉",
        "yaoci": {
            1: "初九：壮于趾，征凶，有孚",
            2: "九二：贞吉",
            3: "九三：小人用壮，君子用罔，贞厉，羝羊触藩，羸其角",
            4: "九四：贞吉悔亡，藩决不羸，壮于大舆之輹",
            5: "六五：丧羊于易，无悔",
            6: "上六：羝羊触藩，不能退，不能遂，无攸利，艰则吉"
        }
    },
    (4, 2): {
        "name": "雷泽归妹", "judgement": "归妹，征凶，无攸利", "description": "泽上有雷，归妹。君子以永终知敝", "fortune": "凶",
        "yaoci": {
            1: "初九：归妹以娣，跛能履，征吉",
            2: "九二：眇能视，利幽人之贞",
            3: "六三：归妹以须，反归以娣",
            4: "九四：归妹愆期，迟归有时",
            5: "六五：帝乙归妹，其君之袂，不如其娣之袂良，月几望，吉",
            6: "上六：女承筐无实，士刲羊无血，无攸利"
        }
    },
    (4, 3): {
        "name": "雷火丰", "judgement": "丰，亨，王假之，勿忧", "description": "雷电皆至，丰。君子以折狱致刑", "fortune": "吉",
        "yaoci": {
            1: "初九：遇其配主，虽旬无咎，往有尚",
            2: "六二：丰其蔀，日中见斗，往得疑疾，有孚发若，吉",
            3: "九三：丰其沛，日中见沫，折其右肱，无咎",
            4: "九四：丰其蔀，日中见斗，遇其夷主，吉",
            5: "六五：来章，有庆誉，吉",
            6: "上六：丰其屋，蔀其家，窥其户，阒其无人，三岁不觌，凶"
        }
    },
    (4, 4): {
        "name": "震为雷", "judgement": "震，亨。震来虩虩，笑言哑哑", "description": "洊雷，震。君子以恐惧修省", "fortune": "中吉",
        "yaoci": {
            1: "初九：震来虩虩，后笑言哑哑，吉",
            2: "六二：震来厉，亿丧贝，跻于九陵，勿逐，七日得",
            3: "六三：震苏苏，震行无眚",
            4: "九四：震遂泥",
            5: "六五：震往来厉，亿无丧，有事",
            6: "上六：震索索，视矍矍，征凶，震不于其躬，于其邻，无咎，婚媾有言"
        }
    },
    (4, 5): {
        "name": "雷风恒", "judgement": "恒，亨，无咎，利贞", "description": "雷风，恒。君子以立不易方", "fortune": "吉",
        "yaoci": {
            1: "初六：浚恒，贞凶，无攸利",
            2: "九二：悔亡",
            3: "九三：不恒其德，或承之羞，贞吝",
            4: "九四：田无禽",
            5: "六五：恒其德，贞，妇人吉，夫子凶",
            6: "上六：振恒，凶"
        }
    },
    (4, 6): {
        "name": "雷水解", "judgement": "解，利西南，无所往", "description": "雷雨作，解。君子以赦过宥罪", "fortune": "吉",
        "yaoci": {
            1: "初六：无咎",
            2: "九二：田获三狐，得黄矢，贞吉",
            3: "六三：负且乘，致寇至，贞吝",
            4: "九四：解而拇，朋至斯孚",
            5: "六五：君子维有解，吉，有孚于小人",
            6: "上六：公用射隼于高墉之上，获之，无不利"
        }
    },
    (4, 7): {
        "name": "雷山小过", "judgement": "小过，亨，利贞，可小事", "description": "山上有雷，小过。君子以行过乎恭", "fortune": "中",
        "yaoci": {
            1: "初六：飞鸟以凶",
            2: "六二：过其祖，遇其妣，不及其君，遇其臣，无咎",
            3: "九三：弗过防之，从或戕之，凶",
            4: "九四：无咎，弗过遇之，往厉必戒，勿用永贞",
            5: "六五：密云不雨，自我西郊，公弋取彼在穴",
            6: "上六：弗遇过之，飞鸟离之，凶，是谓灾眚"
        }
    },
    (4, 8): {
        "name": "雷地豫", "judgement": "豫，利建侯行师", "description": "雷出地奋，豫。先王以作乐崇德", "fortune": "吉",
        "yaoci": {
            1: "初六：鸣豫，凶",
            2: "六二：介于石，不终日，贞吉",
            3: "六三：盱豫，悔，迟有悔",
            4: "九四：由豫，大有得，勿疑，朋盍簪",
            5: "六五：贞疾，恒不死",
            6: "上六：冥豫，成有渝，无咎"
        }
    },
    (5, 1): {
        "name": "风天小畜", "judgement": "小畜，亨，密云不雨", "description": "风行天上，小畜。君子以懿文德", "fortune": "中吉",
        "yaoci": {
            1: "初九：复自道，何其咎，吉",
            2: "九二：牵复，吉",
            3: "九三：舆说辐，夫妻反目",
            4: "六四：有孚，血去惕出，无咎",
            5: "九五：有孚挛如，富以其邻",
            6: "上九：既雨既处，尚德载，妇贞厉，月几望，君子征凶"
        }
    },
    (5, 2): {
        "name": "风泽中孚", "judgement": "中孚，豚鱼吉，利涉大川", "description": "泽上有风，中孚。君子以议狱缓死", "fortune": "吉",
        "yaoci": {
            1: "初九：虞吉，有它不燕",
            2: "九二：鸣鹤在阴，其子和之，我有好爵，吾与尔靡之",
            3: "六三：得敌，或鼓或罢，或泣或歌",
            4: "六四：月几望，马匹亡，无咎",
            5: "九五：有孚挛如，无咎",
            6: "上九：翰音登于天，贞凶"
        }
    },
    (5, 3): {
        "name": "风火家人", "judgement": "家人，利女贞", "description": "风自火出，家人。君子以言有物而行有恒", "fortune": "吉",
        "yaoci": {
            1: "初九：闲有家，悔亡",
            2: "六二：无攸遂，在中馈，贞吉",
            3: "九三：家人嗃嗃，悔厉吉，妇子嘻嘻，终吝",
            4: "六四：富家，大吉",
            5: "九五：王假有家，勿恤吉",
            6: "上九：有孚威如，终吉"
        }
    },
    (5, 4): {
        "name": "风雷益", "judgement": "益，利有攸往，利涉大川", "description": "风雷，益。君子以见善则迁，有过则改", "fortune": "大吉",
        "yaoci": {
            1: "初九：利用为大作，元吉，无咎",
            2: "六二：或益之十朋之龟，弗克违，永贞吉，王用享于帝，吉",
            3: "六三：益之用凶事，无咎，有孚中行，告公用圭",
            4: "六四：中行，告公从，利用为依迁国",
            5: "九五：有孚惠心，勿问元吉，有孚惠我德",
            6: "上九：莫益之，或击之，立心勿恒，凶"
        }
    },
    (5, 5): {
        "name": "巽为风", "judgement": "巽，小亨，利有攸往", "description": "随风，巽。君子以申命行事", "fortune": "吉",
        "yaoci": {
            1: "初六：进退，利武人之贞",
            2: "九二：巽在床下，用史巫纷若，吉无咎",
            3: "九三：频巽，吝",
            4: "六四：悔亡，田获三品",
            5: "九五：贞吉悔亡，无不利，无初有终，先庚三日，后庚三日，吉",
            6: "上九：巽在床下，丧其资斧，贞凶"
        }
    },
    (5, 6): {
        "name": "风水涣", "judgement": "涣，亨，王假有庙", "description": "风行水上，涣。先王以享于帝立庙", "fortune": "中",
        "yaoci": {
            1: "初六：用拯马壮，吉",
            2: "九二：涣奔其机，悔亡",
            3: "六三：涣其躬，无悔",
            4: "六四：涣其群，元吉，涣有丘，匪夷所思",
            5: "九五：涣汗其大号，涣王居，无咎",
            6: "上九：涣其血，去逖出，无咎"
        }
    },
    (5, 7): {
        "name": "风山渐", "judgement": "渐，女归吉，利贞", "description": "山上有木，渐。君子以居贤德善俗", "fortune": "吉",
        "yaoci": {
            1: "初六：鸿渐于干，小子厉，有言，无咎",
            2: "六二：鸿渐于磐，饮食衎衎，吉",
            3: "九三：鸿渐于陆，夫征不复，妇孕不育，凶，利御寇",
            4: "六四：鸿渐于木，或得其桷，无咎",
            5: "九五：鸿渐于陵，妇三岁不孕，终莫之胜，吉",
            6: "上九：鸿渐于陆，其羽可用为仪，吉"
        }
    },
    (5, 8): {
        "name": "风地观", "judgement": "观，盥而不荐，有孚颙若", "description": "风行地上，观。先王以省方观民设教", "fortune": "中吉",
        "yaoci": {
            1: "初六：童观，小人无咎，君子吝",
            2: "六二：窥观，利女贞",
            3: "六三：观我生，进退",
            4: "六四：观国之光，利用宾于王",
            5: "九五：观我生，君子无咎",
            6: "上九：观其生，君子无咎"
        }
    },
    (6, 1): {
        "name": "水天需", "judgement": "需，有孚，光亨，贞吉", "description": "云上于天，需。君子以饮食宴乐", "fortune": "吉",
        "yaoci": {
            1: "初九：需于郊，利用恒，无咎",
            2: "九二：需于沙，小有言，终吉",
            3: "九三：需于泥，致寇至",
            4: "六四：需于血，出自穴",
            5: "九五：需于酒食，贞吉",
            6: "上六：入于穴，有不速之客三人来，敬之终吉"
        }
    },
    (6, 2): {
        "name": "水泽节", "judgement": "节，亨，苦节不可贞", "description": "泽上有水，节。君子以制数度，议德行", "fortune": "中吉",
        "yaoci": {
            1: "初九：不出户庭，无咎",
            2: "九二：不出门庭，凶",
            3: "六三：不节若，则嗟若，无咎",
            4: "六四：安节，亨",
            5: "九五：甘节，吉，往有尚",
            6: "上六：苦节，贞凶，悔亡"
        }
    },
    (6, 3): {
        "name": "水火既济", "judgement": "既济，亨小，利贞", "description": "水在火上，既济。君子以思患而预防之", "fortune": "吉",
        "yaoci": {
            1: "初九：曳其轮，濡其尾，无咎",
            2: "六二：妇丧其茀，勿逐，七日得",
            3: "九三：高宗伐鬼方，三年克之，小人勿用",
            4: "六四：繻有衣袽，终日戒",
            5: "九五：东邻杀牛，不如西邻之禴祭，实受其福",
            6: "上六：濡其首，厉"
        }
    },
    (6, 4): {
        "name": "水雷屯", "judgement": "屯，元亨利贞，勿用有攸往", "description": "云雷，屯。君子以经纶", "fortune": "中",
        "yaoci": {
            1: "初九：磐桓，利居贞，利建侯",
            2: "六二：屯如邅如，乘马班如，匪寇婚媾，女子贞不字，十年乃字",
            3: "六三：即鹿无虞，惟入于林中，君子几不如舍，往吝",
            4: "六四：乘马班如，求婚媾，往吉，无不利",
            5: "九五：屯其膏，小贞吉，大贞凶",
            6: "上六：乘马班如，泣血涟如"
        }
    },
    (6, 5): {
        "name": "水风井", "judgement": "井，改邑不改井，无丧无得", "description": "木上有水，井。君子以劳民劝相", "fortune": "中吉",
        "yaoci": {
            1: "初六：井泥不食，旧井无禽",
            2: "九二：井谷射鲋，瓮敝漏",
            3: "九三：井渫不食，为我心恻，可用汲，王明，并受其福",
            4: "六四：井甃，无咎",
            5: "九五：井冽，寒泉食",
            6: "上六：井收勿幕，有孚元吉"
        }
    },
    (6, 6): {
        "name": "坎为水", "judgement": "习坎，有孚，维心亨", "description": "水洊至，习坎。君子以常德行，习教事", "fortune": "凶",
        "yaoci": {
            1: "初六：习坎，入于坎窞，凶",
            2: "九二：坎有险，求小得",
            3: "六三：来之坎坎，险且枕，入于坎窞，勿用",
            4: "六四：樽酒簋贰，用缶，纳约自牖，终无咎",
            5: "九五：坎不盈，祗既平，无咎",
            6: "上六：系用徽纆，寘于丛棘，三岁不得，凶"
        }
    },
    (6, 7): {
        "name": "水山蹇", "judgement": "蹇，利西南，不利东北", "description": "山上有水，蹇。君子以反身修德", "fortune": "凶",
        "yaoci": {
            1: "初六：往蹇，来誉",
            2: "六二：王臣蹇蹇，匪躬之故",
            3: "九三：往蹇来反",
            4: "六四：往蹇来连",
            5: "九五：大蹇朋来",
            6: "上六：往蹇来硕，吉，利见大人"
        }
    },
    (6, 8): {
        "name": "水地比", "judgement": "比，吉，原筮元永贞", "description": "地上有水，比。先王以建万国，亲诸侯", "fortune": "吉",
        "yaoci": {
            1: "初六：有孚比之，无咎，有孚盈缶，终来有它，吉",
            2: "六二：比之自内，贞吉",
            3: "六三：比之匪人",
            4: "六四：外比之，贞吉",
            5: "九五：显比，王用三驱，失前禽，邑人不诫，吉",
            6: "上六：比之无首，凶"
        }
    },
    (7, 1): {
        "name": "山天大畜", "judgement": "大畜，利贞，不家食吉", "description": "天在山中，大畜。君子以多识前言往行", "fortune": "大吉",
        "yaoci": {
            1: "初九：有厉利已",
            2: "九二：舆说輹",
            3: "九三：良马逐，利艰贞，曰闲舆卫，利有攸往",
            4: "六四：童牛之牿，元吉",
            5: "六五：豮豕之牙，吉",
            6: "上九：何天之衢，亨"
        }
    },
    (7, 2): {
        "name": "山泽损", "judgement": "损，有孚，元吉，无咎", "description": "山下有泽，损。君子以惩忿窒欲", "fortune": "中",
        "yaoci": {
            1: "初九：已事遄往，无咎，酌损之",
            2: "九二：利贞，征凶，弗损益之",
            3: "六三：三人行，则损一人，一人行，则得其友",
            4: "六四：损其疾，使遄有喜，无咎",
            5: "六五：或益之十朋之龟，弗克违，元吉",
            6: "上九：弗损益之，无咎，贞吉，利有攸往，得臣无家"
        }
    },
    (7, 3): {
        "name": "山火贲", "judgement": "贲，亨，小利有攸往", "description": "山下有火，贲。君子以明庶政", "fortune": "吉",
        "yaoci": {
            1: "初九：贲其趾，舍车而徒",
            2: "六二：贲其须",
            3: "九三：贲如濡如，永贞吉",
            4: "六四：贲如皤如，白马翰如，匪寇婚媾",
            5: "六五：贲于丘园，束帛戋戋，吝，终吉",
            6: "上九：白贲，无咎"
        }
    },
    (7, 4): {
        "name": "山雷颐", "judgement": "颐，贞吉，观颐，自求口实", "description": "山下有雷，颐。君子以慎言语，节饮食", "fortune": "中吉",
        "yaoci": {
            1: "初九：舍尔灵龟，观我朵颐，凶",
            2: "六二：颠颐，拂经，于丘颐，征凶",
            3: "六三：拂颐，贞凶，十年勿用，无攸利",
            4: "六四：颠颐吉，虎视眈眈，其欲逐逐，无咎",
            5: "六五：拂经，居贞吉，不可涉大川",
            6: "上九：由颐，厉吉，利涉大川"
        }
    },
    (7, 5): {
        "name": "山风蛊", "judgement": "蛊，元亨，利涉大川", "description": "山下有风，蛊。君子以振民育德", "fortune": "中",
        "yaoci": {
            1: "初六：干父之蛊，有子，考无咎，厉终吉",
            2: "九二：干母之蛊，不可贞",
            3: "九三：干父之蛊，小有悔，无大咎",
            4: "六四：裕父之蛊，往见吝",
            5: "六五：干父之蛊，用誉",
            6: "上九：不事王侯，高尚其事"
        }
    },
    (7, 6): {
        "name": "山水蒙", "judgement": "蒙，亨，匪我求童蒙", "description": "山下出泉，蒙。君子以果行育德", "fortune": "中吉",
        "yaoci": {
            1: "初六：发蒙，利用刑人，用说桎梏，以往吝",
            2: "九二：包蒙吉，纳妇吉，子克家",
            3: "六三：勿用取女，见金夫，不有躬，无攸利",
            4: "六四：困蒙，吝",
            5: "六五：童蒙，吉",
            6: "上九：击蒙，不利为寇，利御寇"
        }
    },
    (7, 7): {
        "name": "艮为山", "judgement": "艮其背，不获其身", "description": "兼山，艮。君子以思不出其位", "fortune": "中",
        "yaoci": {
            1: "初六：艮其趾，无咎，利永贞",
            2: "六二：艮其腓，不拯其随，其心不快",
            3: "九三：艮其限，列其夤，厉薰心",
            4: "六四：艮其身，无咎",
            5: "六五：艮其辅，言有序，悔亡",
            6: "上九：敦艮，吉"
        }
    },
    (7, 8): {
        "name": "山地剥", "judgement": "剥，不利有攸往", "description": "山附于地，剥。上以厚下安宅", "fortune": "凶",
        "yaoci": {
            1: "初六：剥床以足，蔑贞凶",
            2: "六二：剥床以辨，蔑贞凶",
            3: "六三：剥之，无咎",
            4: "六四：剥床以肤，凶",
            5: "六五：贯鱼，以宫人宠，无不利",
            6: "上九：硕果不食，君子得舆，小人剥庐"
        }
    },
    (8, 1): {
        "name": "地天泰", "judgement": "泰，小往大来，吉亨", "description": "天地交，泰。后以财成天地之道", "fortune": "大吉",
        "yaoci": {
            1: "初九：拔茅茹，以其汇，征吉",
            2: "九二：包荒，用冯河，不遐遗，朋亡，得尚于中行",
            3: "九三：无平不陂，无往不复，艰贞无咎，勿恤其孚，于食有福",
            4: "六四：翩翩不富，以其邻，不戒以孚",
            5: "六五：帝乙归妹，以祉元吉",
            6: "上六：城复于隍，勿用师，自邑告命，贞吝"
        }
    },
    (8, 2): {
        "name": "地泽临", "judgement": "临，元亨利贞", "description": "泽上有地，临。君子以教思无穷", "fortune": "吉",
        "yaoci": {
            1: "初九：咸临，贞吉",
            2: "九二：咸临，吉无不利",
            3: "六三：甘临，无攸利，既忧之，无咎",
            4: "六四：至临，无咎",
            5: "六五：知临，大君之宜，吉",
            6: "上六：敦临，吉，无咎"
        }
    },
    (8, 3): {
        "name": "地火明夷", "judgement": "明夷，利艰贞", "description": "明入地中，明夷。君子以莅众用晦而明", "fortune": "凶",
        "yaoci": {
            1: "初九：明夷于飞，垂其翼，君子于行，三日不食，有攸往，主人有言",
            2: "六二：明夷，夷于左股，用拯马壮，吉",
            3: "九三：明夷于南狩，得其大首，不可疾贞",
            4: "六四：入于左腹，获明夷之心，于出门庭",
            5: "六五：箕子之明夷，利贞",
            6: "上六：不明晦，初登于天，后入于地"
        }
    },
    (8, 4): {
        "name": "地雷复", "judgement": "复，亨，出入无疾", "description": "雷在地中，复。先王以至日闭关", "fortune": "吉",
        "yaoci": {
            1: "初九：不远复，无祗悔，元吉",
            2: "六二：休复，吉",
            3: "六三：频复，厉无咎",
            4: "六四：中行独复",
            5: "六五：敦复，无悔",
            6: "上六：迷复，凶，有灾眚，用行师，终有大败，以其国君，凶，至于十年，不克征"
        }
    },
    (8, 5): {
        "name": "地风升", "judgement": "升，元亨，用见大人", "description": "地中生木，升。君子以顺德，积小以高大", "fortune": "大吉",
        "yaoci": {
            1: "初六：允升，大吉",
            2: "九二：孚乃利用禴，无咎",
            3: "九三：升虚邑",
            4: "六四：王用亨于岐山，吉，无咎",
            5: "六五：贞吉，升阶",
            6: "上六：冥升，利于不息之贞"
        }
    },
    (8, 6): {
        "name": "地水师", "judgement": "师，贞，丈人吉，无咎", "description": "地中有水，师。君子以容民畜众", "fortune": "中吉",
        "yaoci": {
            1: "初六：师出以律，否臧凶",
            2: "九二：在师中，吉无咎，王三锡命",
            3: "六三：师或舆尸，凶",
            4: "六四：师左次，无咎",
            5: "六五：田有禽，利执言，无咎，长子帅师，弟子舆尸，贞凶",
            6: "上六：大君有命，开国承家，小人勿用"
        }
    },
    (8, 7): {
        "name": "地山谦", "judgement": "谦，亨，君子有终", "description": "地中有山，谦。君子以裒多益寡", "fortune": "吉",
        "yaoci": {
            1: "初六：谦谦君子，用涉大川，吉",
            2: "六二：鸣谦，贞吉",
            3: "九三：劳谦，君子有终，吉",
            4: "六四：无不利，撝谦",
            5: "六五：不富以其邻，利用侵伐，无不利",
            6: "上六：鸣谦，利用行师，征邑国"
        }
    },
    (8, 8): {
        "name": "坤为地", "judgement": "元亨，利牝马之贞", "description": "地势坤，君子以厚德载物", "fortune": "大吉",
        "yaoci": {
            1: "初六：履霜，坚冰至",
            2: "六二：直方大，不习无不利",
            3: "六三：含章可贞，或从王事，无成有终",
            4: "六四：括囊，无咎，无誉",
            5: "六五：黄裳，元吉",
            6: "上六：龙战于野，其血玄黄"
        }
    },
}

# 天干地支
TIANGAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
DIZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
SHENGXIAO = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"]

# 五行关系
WUXING = {
    "金": {"color": "#FFD700", "generates": "水", "overcomes": "木", "generated_by": "土", "overcome_by": "火"},
    "木": {"color": "#228B22", "generates": "火", "overcomes": "土", "generated_by": "水", "overcome_by": "金"},
    "水": {"color": "#4169E1", "generates": "木", "overcomes": "火", "generated_by": "金", "overcome_by": "土"},
    "火": {"color": "#FF4500", "generates": "土", "overcomes": "金", "generated_by": "木", "overcome_by": "水"},
    "土": {"color": "#8B4513", "generates": "金", "overcomes": "水", "generated_by": "火", "overcome_by": "木"},
}

# 月令旺衰（农历月份对应五行旺衰）
YUELING = {
    1: {"旺": "木", "相": "火", "休": "水", "囚": "金", "死": "土"},   # 正月寅，木旺
    2: {"旺": "木", "相": "火", "休": "水", "囚": "金", "死": "土"},   # 二月卯，木旺
    3: {"旺": "土", "相": "金", "休": "火", "囚": "木", "死": "水"},   # 三月辰，土旺
    4: {"旺": "火", "相": "土", "休": "木", "囚": "水", "死": "金"},   # 四月巳，火旺
    5: {"旺": "火", "相": "土", "休": "木", "囚": "水", "死": "金"},   # 五月午，火旺
    6: {"旺": "土", "相": "金", "休": "火", "囚": "木", "死": "水"},   # 六月未，土旺
    7: {"旺": "金", "相": "水", "休": "土", "囚": "火", "死": "木"},   # 七月申，金旺
    8: {"旺": "金", "相": "水", "休": "土", "囚": "火", "死": "木"},   # 八月酉，金旺
    9: {"旺": "土", "相": "金", "休": "火", "囚": "木", "死": "水"},   # 九月戌，土旺
    10: {"旺": "水", "相": "木", "休": "金", "囚": "土", "死": "火"},  # 十月亥，水旺
    11: {"旺": "水", "相": "木", "休": "金", "囚": "土", "死": "火"},  # 十一月子，水旺
    12: {"旺": "土", "相": "金", "休": "火", "囚": "木", "死": "水"},  # 十二月丑，土旺
}

# 八卦的六爻表示（从下到上，1为阳爻，0为阴爻）
GUA_YAOS = {
    1: [1, 1, 1],  # 乾：从下往上=阳阳阳
    2: [1, 1, 0],  # 兑：从下往上=阳阳阴
    3: [1, 0, 1],  # 离：从下往上=阳阴阳
    4: [1, 0, 0],  # 震：从下往上=阳阴阴
    5: [0, 1, 1],  # 巽：从下往上=阴阳阳
    6: [0, 1, 0],  # 坎：从下往上=阴阳阴
    7: [0, 0, 1],  # 艮：从下往上=阴阴阳
    8: [0, 0, 0],  # 坤：从下往上=阴阴阴
}

YAOS_TO_GUA = {
    (1, 1, 1): 1,  # 乾
    (1, 1, 0): 2,  # 兑
    (1, 0, 1): 3,  # 离
    (1, 0, 0): 4,  # 震
    (0, 1, 1): 5,  # 巽
    (0, 1, 0): 6,  # 坎
    (0, 0, 1): 7,  # 艮
    (0, 0, 0): 8,  # 坤
}

class LunarConversionError(Exception):
    """农历转换失败异常"""
    pass


def solar_to_lunar(year, month, day):
    """
    公历转农历
    返回：(农历年, 农历月, 农历日, 是否闰月)
    
    zhdate库使用 leap_month 布尔属性表示是否为闰月
    转换失败时抛出 LunarConversionError 异常
    """
    try:
        lunar = ZhDate.from_datetime(datetime(year, month, day))
        lunar_year = lunar.lunar_year
        lunar_month = lunar.lunar_month
        lunar_day = lunar.lunar_day
        
        # zhdate库使用leap_month属性（布尔值）表示是否闰月
        is_leap = getattr(lunar, 'leap_month', False)
        
        return lunar_year, lunar_month, lunar_day, is_leap
    except (ValueError, TypeError) as e:
        # 农历转换失败，抛出明确错误
        raise LunarConversionError(f"农历转换失败：公历 {year}-{month}-{day} 无法转换为农历，原因：{str(e)}")


def get_ganzhi_year(lunar_year):
    """计算农历年份的天干地支"""
    gan_idx = (lunar_year - 4) % 10
    zhi_idx = (lunar_year - 4) % 12
    return TIANGAN[gan_idx] + DIZHI[zhi_idx], SHENGXIAO[zhi_idx]


def get_ganzhi_month(lunar_year, lunar_month):
    """计算农历月份的天干地支"""
    year_gan = (lunar_year - 4) % 10
    month_gan_base = [2, 4, 6, 8, 0, 2, 4, 6, 8, 0]
    gan_idx = (month_gan_base[year_gan] + lunar_month - 1) % 10
    zhi_idx = (lunar_month + 1) % 12
    return TIANGAN[gan_idx] + DIZHI[zhi_idx]


def get_ganzhi_day(year, month, day):
    """
    计算日期的天干地支
    基准：1900年1月1日是甲戌日（甲=0，戌=10）
    """
    from datetime import date
    base = date(1900, 1, 1)
    current = date(year, month, day)
    diff = (current - base).days
    gan_idx = diff % 10  # 甲=0
    zhi_idx = (diff + 10) % 12  # 戌=10
    return TIANGAN[gan_idx] + DIZHI[zhi_idx]


def get_shichen(hour):
    """
    获取时辰
    时辰划分：子(23-01), 丑(01-03), 寅(03-05), 卯(05-07), 辰(07-09), 巳(09-11),
             午(11-13), 未(13-15), 申(15-17), 酉(17-19), 戌(19-21), 亥(21-23)
    """
    shichen_names = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    # 子时跨天特殊处理：23:00-00:59都是子时
    if hour == 23 or hour == 0:
        idx = 0
    else:
        # 其他时辰：1-2丑，3-4寅，5-6卯，7-8辰，9-10巳，11-12午，
        # 13-14未，15-16申，17-18酉，19-20戌，21-22亥
        idx = ((hour + 1) // 2) % 12
    return shichen_names[idx] + "时", idx + 1


def calculate_gua(lunar_year, lunar_month, lunar_day, shichen_num):
    """
    梅花易数时间起卦法
    上卦：(年支数+月数+日数) ÷ 8 取余
    下卦：(年支数+月数+日数+时辰数) ÷ 8 取余
    动爻：(年支数+月数+日数+时辰数) ÷ 6 取余
    
    年支数：子=1, 丑=2, 寅=3, 卯=4, 辰=5, 巳=6, 午=7, 未=8, 申=9, 酉=10, 戌=11, 亥=12
    """
    # 公元4年为甲子年(子=1)
    # (year-4)%12 得到地支索引(0-11)，+1 得到地支数(1-12)
    # 例：2024年辰年 → (2024-4)%12=4, 4+1=5 ✓
    # 例：2008年子年 → (2008-4)%12=0, 0+1=1 ✓
    # 例：2019年亥年 → (2019-4)%12=11, 11+1=12 ✓
    year_zhi = ((lunar_year - 4) % 12) + 1
    
    # 计算上卦
    upper_sum = year_zhi + lunar_month + lunar_day
    upper_rem = upper_sum % 8  # 原始余数
    upper_gua = upper_rem if upper_rem != 0 else 8  # 余数为0则取8
    
    # 计算下卦（加上时辰）
    lower_sum = upper_sum + shichen_num
    lower_rem = lower_sum % 8  # 原始余数
    lower_gua = lower_rem if lower_rem != 0 else 8  # 余数为0则取8
    
    # 计算动爻（用下卦总数）
    dong_yao_rem = lower_sum % 6  # 原始余数
    dong_yao = dong_yao_rem if dong_yao_rem != 0 else 6  # 余数为0则取6
    
    return upper_gua, lower_gua, dong_yao, {
        "year_zhi": year_zhi,
        "lunar_month": lunar_month,
        "lunar_day": lunar_day,
        "shichen_num": shichen_num,
        "upper_sum": upper_sum,
        "lower_sum": lower_sum,
        "yao_sum": lower_sum,  # 动爻计算用的是下卦总数
        # 保留原始余数用于展示
        "upper_rem": upper_rem,
        "lower_rem": lower_rem,
        "dong_yao_rem": dong_yao_rem
    }


def get_hu_gua(upper, lower):
    """
    计算互卦
    互卦：取本卦2、3、4爻为下卦，3、4、5爻为上卦
    
    注意：六爻顺序是从下往上
    索引：0=初爻(1)，1=二爻(2)，2=三爻(3)，3=四爻(4)，4=五爻(5)，5=上爻(6)
    """
    # 确保GUA_YAOS是从下往上的顺序
    # 如果GUA_YAOS是下卦/上卦的内部顺序（从下往上）
    lower_yaos = GUA_YAOS[lower]  # 下卦三爻：[初爻, 二爻, 三爻]
    upper_yaos = GUA_YAOS[upper]  # 上卦三爻：[四爻, 五爻, 上爻]
    
    # 构建完整的六爻（从下往上）
    six_yaos = lower_yaos + upper_yaos  # [初, 二, 三, 四, 五, 上]
    
    # 互卦下卦：取第2、3、4爻（索引1,2,3）
    hu_lower_yaos = (six_yaos[1], six_yaos[2], six_yaos[3])
    # 互卦上卦：取第3、4、5爻（索引2,3,4）
    hu_upper_yaos = (six_yaos[2], six_yaos[3], six_yaos[4])
    
    # 查找对应的卦
    hu_lower = YAOS_TO_GUA.get(hu_lower_yaos)
    hu_upper = YAOS_TO_GUA.get(hu_upper_yaos)
    
    if hu_lower is None or hu_upper is None:
        raise ValueError(f"无法找到对应的卦：下卦={hu_lower_yaos}, 上卦={hu_upper_yaos}")
    
    return hu_upper, hu_lower


def get_bian_gua(upper, lower, dong_yao):
    """计算变卦"""
    lower_yaos = list(GUA_YAOS[lower])
    upper_yaos = list(GUA_YAOS[upper])
    six_yaos = lower_yaos + upper_yaos
    
    six_yaos[dong_yao - 1] = 1 - six_yaos[dong_yao - 1]
    
    new_lower_yaos = tuple(six_yaos[0:3])
    new_upper_yaos = tuple(six_yaos[3:6])
    
    new_lower = YAOS_TO_GUA[new_lower_yaos]
    new_upper = YAOS_TO_GUA[new_upper_yaos]
    
    return new_upper, new_lower


# 五行关系标准枚举（用于逻辑判断）
# 统一命名：比和 / 上生下 / 下生上 / 上克下 / 下克上
WUXING_RELATION = {
    "比和": "比和",      # 同五行
    "上生下": "泄",       # 上卦五行生下卦五行
    "下生上": "生",       # 下卦五行生上卦五行
    "上克下": "克",       # 上卦五行克下卦五行
    "下克上": "被克"      # 下卦五行克上卦五行
}


def analyze_wuxing_relation(element1, element2):
    """
    分析五行关系（element1 对 element2 的关系）
    返回：(标准关系枚举, 显示描述)
    """
    if element1 == element2:
        return "比和", "势均力敌，平稳之象"
    if WUXING[element1]["generates"] == element2:
        # element1 生 element2 = 上生下（泄气）
        return "上生下", f"{element1}生{element2}，气泄之象"
    if WUXING[element1]["generated_by"] == element2:
        # element2 生 element1 = 下生上（得助）
        return "下生上", f"{element2}生{element1}，得助之象"
    if WUXING[element1]["overcomes"] == element2:
        # element1 克 element2 = 上克下
        return "上克下", f"{element1}克{element2}，制约之象"
    if WUXING[element1]["overcome_by"] == element2:
        # element2 克 element1 = 下克上（受制）
        return "下克上", f"{element2}克{element1}，受制之象"
    return "无直接关系", ""


def analyze_ti_yong(upper, lower, dong_yao):
    """
    体用分析
    体卦：无动爻的卦，代表问卦主体
    用卦：有动爻的卦，代表外部环境
    动爻1-3在下卦，则下卦为用，上卦为体
    动爻4-6在上卦，则上卦为用，下卦为体
    
    关系统一使用标准枚举：比和 / 用生体 / 体生用 / 体克用 / 用克体
    """
    if dong_yao <= 3:
        ti_gua = upper  # 上卦为体
        yong_gua = lower  # 下卦为用
        ti_pos = "上卦"
        yong_pos = "下卦"
    else:
        ti_gua = lower  # 下卦为体
        yong_gua = upper  # 上卦为用
        ti_pos = "下卦"
        yong_pos = "上卦"
    
    ti_element = BAGUA[ti_gua]['element']
    yong_element = BAGUA[yong_gua]['element']
    
    # 分析体用生克关系（使用统一的标准命名）
    if ti_element == yong_element:
        relation = "比和"
        relation_type = "比和"  # 标准类型
        fortune = "平"
        analysis = "体用比和，势均力敌，事可成但需努力"
    elif WUXING[yong_element]["generates"] == ti_element:
        relation = "用生体"
        relation_type = "生"    # 体得生助
        fortune = "吉"
        analysis = "用生体，外部环境助益主体，事顺利，有贵人相助"
    elif WUXING[ti_element]["generates"] == yong_element:
        relation = "体生用"
        relation_type = "泄"    # 体气外泄
        fortune = "耗"
        analysis = "体生用，主体气泄，付出多回报少，宜守不宜进"
    elif WUXING[ti_element]["overcomes"] == yong_element:
        relation = "体克用"
        relation_type = "克"    # 体制用
        fortune = "平"
        analysis = "体克用，主体制约环境，需努力可成，先难后易"
    elif WUXING[yong_element]["overcomes"] == ti_element:
        relation = "用克体"
        relation_type = "被克"  # 体受制
        fortune = "凶"
        analysis = "用克体，外部压力大，阻碍重重，宜退避观望"
    else:
        relation = "无直接关系"
        relation_type = "无"
        fortune = "平"
        analysis = "体用关系不明显"
    
    return {
        "ti_gua": {
            "name": BAGUA[ti_gua]['name'],
            "symbol": BAGUA[ti_gua]['symbol'],
            "element": ti_element,
            "position": ti_pos
        },
        "yong_gua": {
            "name": BAGUA[yong_gua]['name'],
            "symbol": BAGUA[yong_gua]['symbol'],
            "element": yong_element,
            "position": yong_pos
        },
        "relation": relation,           # 体用关系（显示用）
        "relation_type": relation_type, # 标准关系类型（逻辑判断用）
        "fortune": fortune,
        "analysis": analysis
    }


def get_yueling_analysis(lunar_month, ti_element):
    """月令旺衰分析"""
    yueling = YUELING.get(lunar_month, YUELING[1])
    
    if yueling["旺"] == ti_element:
        status = "旺"
        desc = f"体卦{ti_element}当令得时，气势旺盛，主事易成"
    elif yueling["相"] == ti_element:
        status = "相"
        desc = f"体卦{ti_element}得令之相，气势较旺，事有助力"
    elif yueling["休"] == ti_element:
        status = "休"
        desc = f"体卦{ti_element}休囚，气势平平，需借外力"
    elif yueling["囚"] == ti_element:
        status = "囚"
        desc = f"体卦{ti_element}受囚，力量受制，行事宜缓"
    elif yueling["死"] == ti_element:
        status = "死"
        desc = f"体卦{ti_element}失令，力量最弱，宜守不宜进"
    else:
        status = "平"
        desc = "月令对体卦影响不大"
    
    return {
        "status": status,
        "wang_element": yueling["旺"],
        "description": desc
    }


def _format_upper_calc(year_zhi, lunar_month, lunar_day, total, rem, gua_name):
    """
    格式化上卦计算过程的展示
    展示完整的加法过程和取余过程
    """
    formula = f"({year_zhi}+{lunar_month}+{lunar_day})"
    if rem == 0:
        return f"{formula} % 8 = {total} % 8 = 0 → 8（{gua_name}）"
    else:
        return f"{formula} % 8 = {total} % 8 = {rem}（{gua_name}）"


def _format_lower_calc(year_zhi, lunar_month, lunar_day, shichen, total, rem, gua_name):
    """
    格式化下卦计算过程的展示
    展示完整的加法过程和取余过程
    """
    formula = f"({year_zhi}+{lunar_month}+{lunar_day}+{shichen})"
    if rem == 0:
        return f"{formula} % 8 = {total} % 8 = 0 → 8（{gua_name}）"
    else:
        return f"{formula} % 8 = {total} % 8 = {rem}（{gua_name}）"


def _format_yao_calc(year_zhi, lunar_month, lunar_day, shichen, total, rem, final):
    """
    格式化动爻计算过程的展示
    展示完整的加法过程和取余过程
    """
    formula = f"({year_zhi}+{lunar_month}+{lunar_day}+{shichen})"
    if rem == 0:
        return f"{formula} % 6 = {total} % 6 = 0 → 6（第六爻）"
    else:
        return f"{formula} % 6 = {total} % 6 = {rem}（第{final}爻）"


def get_gua_info(upper, lower, dong_yao=None):
    """获取卦象信息"""
    upper_info = BAGUA[upper]
    lower_info = BAGUA[lower]
    
    hexagram_key = (upper, lower)
    hexagram = HEXAGRAMS.get(hexagram_key, {
        "name": f"{upper_info['name']}{lower_info['name']}卦",
        "judgement": "待查",
        "description": "待查",
        "fortune": "中",
        "yaoci": {}
    })
    
    result = {
        "name": hexagram['name'],
        "upper": {
            "name": upper_info['name'],
            "symbol": upper_info['symbol'],
            "nature": upper_info['nature'],
            "element": upper_info['element'],
            "direction": upper_info['direction'],
            "attribute": upper_info['attribute'],
            "number": upper_info['number']
        },
        "lower": {
            "name": lower_info['name'],
            "symbol": lower_info['symbol'],
            "nature": lower_info['nature'],
            "element": lower_info['element'],
            "direction": lower_info['direction'],
            "attribute": lower_info['attribute'],
            "number": lower_info['number']
        },
        "judgement": hexagram['judgement'],
        "description": hexagram['description'],
        "fortune": hexagram['fortune']
    }
    
    # 如果有动爻，添加动爻爻辞
    if dong_yao and 'yaoci' in hexagram:
        result['dong_yao_ci'] = hexagram['yaoci'].get(dong_yao, "")
    
    return result


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/divine', methods=['POST'])
def divine():
    """占卜API"""
    data = request.json or {}
    datetime_str = data.get('datetime')
    question = data.get('question', '')
    
    # 1. datetime 缺失或非法时返回 400 错误
    if not datetime_str:
        return jsonify({
            "error": "invalid_datetime",
            "message": "缺少 datetime 参数，请提供有效的日期时间（推荐格式：2025-01-05T14:30:00+08:00）"
        }), 400
    
    try:
        dt = datetime.fromisoformat(datetime_str)
    except (ValueError, TypeError) as e:
        return jsonify({
            "error": "invalid_datetime",
            "message": f"datetime 格式非法：{datetime_str}，请使用 ISO 格式（如：2025-01-05T14:30:00+08:00）"
        }), 400
    
    # 2. 统一时区处理：如果没有时区信息，假定为 +08:00；否则转换到 +08:00
    if dt.tzinfo is None:
        # 无时区信息，假定为中国标准时间
        dt = dt.replace(tzinfo=CHINA_TZ)
    else:
        # 有时区信息，统一转换到中国标准时间
        dt = dt.astimezone(CHINA_TZ)
    
    # 3. 公历转农历（包含闰月信息），失败时返回错误
    try:
        lunar_year, lunar_month, lunar_day, is_leap_month = solar_to_lunar(dt.year, dt.month, dt.day)
    except LunarConversionError as e:
        return jsonify({
            "error": "lunar_conversion_failed",
            "message": str(e)
        }), 400
    
    # 计算干支
    year_gz, shengxiao = get_ganzhi_year(lunar_year)
    # 闰月的月干支与所闰月份相同
    month_gz = get_ganzhi_month(lunar_year, lunar_month)
    day_gz = get_ganzhi_day(dt.year, dt.month, dt.day)
    shichen_name, shichen_num = get_shichen(dt.hour)
    
    # 起卦（闰月按所闰月份计算）
    upper, lower, dong_yao, calc_detail = calculate_gua(lunar_year, lunar_month, lunar_day, shichen_num)
    
    # 记录闰月信息用于显示
    calc_detail['is_leap_month'] = is_leap_month
    
    # 获取本卦信息（含动爻爻辞）
    ben_gua_info = get_gua_info(upper, lower, dong_yao)
    ben_gua_info['dong_yao'] = dong_yao
    
    # 计算互卦
    hu_upper, hu_lower = get_hu_gua(upper, lower)
    hu_gua_info = get_gua_info(hu_upper, hu_lower)
    
    # 计算变卦
    bian_upper, bian_lower = get_bian_gua(upper, lower, dong_yao)
    bian_gua_info = get_gua_info(bian_upper, bian_lower)
    
    # 体用分析
    ti_yong = analyze_ti_yong(upper, lower, dong_yao)
    
    # 月令旺衰
    yueling = get_yueling_analysis(lunar_month, ti_yong['ti_gua']['element'])
    
    # 五行分析（本卦上下卦）
    upper_element = ben_gua_info['upper']['element']
    lower_element = ben_gua_info['lower']['element']
    relation, relation_desc = analyze_wuxing_relation(upper_element, lower_element)
    
    # 构建农历日期字符串（处理闰月显示）
    leap_prefix = "闰" if is_leap_month else ""
    lunar_date_str = f"农历{lunar_year}年{leap_prefix}{lunar_month}月{lunar_day}日"
    
    
    result = {
        "time_info": {
            "solar_date": dt.strftime("%Y年%m月%d日 %H:%M"),
            "lunar_date": lunar_date_str,
            "is_leap_month": is_leap_month,
            "year_ganzhi": year_gz,
            "month_ganzhi": month_gz,
            "day_ganzhi": day_gz,
            "shichen": shichen_name,
            "shengxiao": shengxiao,
            "full_ganzhi": f"{year_gz}年 {month_gz}月 {day_gz}日 {shichen_name}"
        },
        "ben_gua": ben_gua_info,
        "hu_gua": hu_gua_info,
        "bian_gua": bian_gua_info,
        "ti_yong": ti_yong,
        "yueling": yueling,
        "wuxing_analysis": {
            "upper_element": upper_element,
            "lower_element": lower_element,
            "relation": relation,
            "relation_desc": relation_desc,
            "upper_color": WUXING[upper_element]['color'],
            "lower_color": WUXING[lower_element]['color']
        },
        "question": question,
        "calculation_detail": {
            "year_zhi": f"年支数={calc_detail['year_zhi']}",
            "lunar_month": f"月数={calc_detail['lunar_month']}" + ("（闰月，按所闰月份计算）" if is_leap_month else ""),
            "lunar_day": f"日数={calc_detail['lunar_day']}",
            "shichen": f"时辰数={calc_detail['shichen_num']}",
            "upper_calc": _format_upper_calc(
                calc_detail['year_zhi'], calc_detail['lunar_month'], calc_detail['lunar_day'],
                calc_detail['upper_sum'], calc_detail['upper_rem'], BAGUA[upper]['name']
            ),
            "lower_calc": _format_lower_calc(
                calc_detail['year_zhi'], calc_detail['lunar_month'], calc_detail['lunar_day'], calc_detail['shichen_num'],
                calc_detail['lower_sum'], calc_detail['lower_rem'], BAGUA[lower]['name']
            ),
            "dong_yao_calc": _format_yao_calc(
                calc_detail['year_zhi'], calc_detail['lunar_month'], calc_detail['lunar_day'], calc_detail['shichen_num'],
                calc_detail['yao_sum'], calc_detail['dong_yao_rem'], dong_yao
            ),
            "is_leap_month": is_leap_month
        }
    }
    
    return jsonify(result)


@app.route('/api/bagua')
def get_bagua_info_api():
    """获取八卦信息"""
    return jsonify(BAGUA)


@app.route('/api/wuxing')
def get_wuxing_info():
    """获取五行信息"""
    return jsonify(WUXING)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
