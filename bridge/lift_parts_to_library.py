# Lift parts out of a kitbash .blend into the Kitbash Library folders.
#
# Open the .blend in Blender, then Scripting tab > Open > this file > Run Script.
# Leave DRY_RUN on the first time: it writes only the report, so you can check
# where everything would go. Then set DRY_RUN = False and run it again.
#
# For each part it writes:
#   <Library>\<Creator - Mark>\<Kit>\<Type>\<part>.stl
#       the part as you see it in the file (modifiers and scene scale
#       applied, Part Sockets' WS_ print cuts left off), in the part's OWN
#       coordinates, so the STL's origin is the origin you set. The report
#       flags every part whose scale or modifiers were applied.
#   <part>.sockets.json   (only for parts with sockets or per-part fits)
#       the sockets, relative to the part, any Store Per-Part Fit offsets,
#       and the fit types they use, so the TIOW Inbox add-on can rebuild
#       them when the part is imported.
# Fit types are renamed on the way out (RENAME below), so library parts use
# the joint names TIOW Inbox auto-snaps by. Where two of your types become one
# name (arm__Torso_r and HeresyArms_r -> Shoulder R) and some part in the file
# carries a socket of each, the second type's parts are re-based onto the
# first's socket: their STL origin moves by the difference you set up between
# the two sockets, so every arm fits the one Shoulder socket.
# plus a report: <Library>\_lift_report_<blend name>.csv
# and, unless JOINT_SET is "", every captured fit type is saved to
# Part Sockets' Joint Library under that name.
#
# Nothing in the .blend is changed. Existing STLs are left alone unless
# OVERWRITE is True.

LIBRARY = r"E:\Library"        # <- your Library folder
DRY_RUN = True                 # True: report only. False: write the files.
OVERWRITE = False              # True: replace STLs that already exist
JOINT_SET = "Kitbash master"   # "" to skip saving fit types to the Joint Library

# Which part type each collection in the file holds.
COLLECTION_TYPES = {
    "R arm": "Arms", "L Arm": "Arms", "HeresyArms_r": "Arms", "Nartheciumarms_l": "Arms",
    "forearm r": "Arms", "Helmets": "Heads", "Torso": "Chests", "Torso new": "Chests",
    "Backpack": "Backpacks", "WS_import_New backpacks": "Backpacks", "Pauldron": "Shoulder Pads",
    "Right Arm Meele": "Melee", "Claw": "Melee", "Piistols": "Pistols",
    "Two Armed Guns": "Two-Handed Guns", "Two Armed Melee": "Two-Handed Melee",
    "Heavy weapons with cables": "Heavy Weapons", "Shield": "Shields",
    "WS_import_Legs donrrr.001": "Legs", "WS_import_Legs donrrr": "Legs",
    "WS_import_heresey legs": "Legs", "WS_import_base_jumpack": "Jump Packs",
    "Accesorries": "Accessories",
}

# Single parts whose type differs from their collection's.
PART_TYPES = {"base_32_mm_1": "Bases"}

# Your fit type names -> the joint names the library uses. A socket is named
# after the joint it sits on, so several part types can share it (arms,
# two-handed guns and heavy weapons all go on Shoulder R). Types not listed
# keep their name. When two old names map to one new name, list the one whose
# parts should stay put first.
RENAME = {
    "arm__Torso_r": "Shoulder R", "HeresyArms_r": "Shoulder R",
    "Wrist_socket_r": "Hand R", "Wrist_Armout_r": "Forearm R",
    "Shield_to_hand_r": "Shield R", "Head": "Neck", "Backpack": "Back",
    "Primaris back pack topper": "Back Top", "heresy backpack topper": "Back Top",
    "BackPack_fin_r": "Pack Fin R", "BackPack_fin_l": "Pack Fin L",
    "wing_r": "Wing R", "wing_l": "Wing L",
    "Right Hip": "Hip R", "Left Hip": "Hip L", "Tabard": "Belt Front",
    "Legs 1": "Base Pose 1", "Legs 2": "Base Pose 2", "Legs 3": "Base Pose 3",
    "Legs 4": "Base Pose 4", "Legs 5": "Base Pose 5",
    "Jump legs 1": "Base Jump 1", "Jump Legs 2": "Base Jump 2", "Jump legs 3": "Base Jump 3",
    "Jump legs 4": "Base Jump 4", "Jump leg 5": "Base Jump 5", "Jump legs 6": "Base Jump 6",
    "Jump Legs 7": "Base Jump 7", "Jump legs 8": "Base Jump 8",
}

# Which fit type a collection's parts were set up for, when they aren't
# snapped in the file (needed only for types that get merged above).
COLLECTION_FIT = {"HeresyArms_r": "HeresyArms_r", "R arm": "arm__Torso_r"}

# Matched by name and triangle count against Mar Fil's own files:
#   object name -> [library folder for its kit, Mar Fil source file,
#                   source bbox min, source bbox max]
PARTS_JSON = r'''{"1":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Backpacks/BackPackUpdate-1/BackPackUpdate-1/RawSTL/1.stl",[-8.984700202941895,-11.081299781799316,25.926799774169922],[8.984700202941895,-4.370100021362305,40.917999267578125]],"1-Helmet-1":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Helmet-Heads/1-Helmet-1.stl",[-2.3570001125335693,-3.6291000843048096,33.122798919677734],[6.278800010681152,3.629199981689453,41.666500091552734]],"1-Helmet-1-A":["Mar Fil - Tacticus/VeteranBladeSquad","VeteranBladeSquad/VeteranBladeSquad/Helmets/Helmets-RawSTL/1-Helmet-1-A.stl",[-3.5792999267578125,-3.4458000659942627,-2.717600107192993],[4.594399929046631,3.44569993019104,5.395199775695801]],"1-Helmet-A":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Helmets/Helmet-RawStl/1-Helmet-A.stl",[-3.5813000202178955,-3.447700023651123,-2.7190001010894775],[4.622700214385986,3.4477999210357666,5.397500038146973]],"1.001":["_Unsorted/Mar Fil/HelmetsUpdate","HelmetsUpdate/HelmetsUpdates/HelmetsUpdates-1/1.stl",[-2.3570001125335693,-3.6291000843048096,33.122798919677734],[6.27869987487793,3.6291000843048096,41.666900634765625]],"1.002":["_Unsorted/Mar Fil/HelmetsUpdate","HelmetsUpdate/HelmetsUpdates/HelmetsUpdates/1.stl",[-2.3570001125335693,-3.6291000843048096,33.122798919677734],[6.278800010681152,3.629199981689453,41.666500091552734]],"100-Gun-5-B":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/100-Gun-5-B.stl",[-1.7421000003814697,-8.314800262451172,-7.009099960327148],[2.5738000869750977,13.567700386047363,7.6321001052856445]],"101-Arm-6-R-A":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Arms/101-Arm-6-R-A.stl",[-7.142000198364258,-2.998199939727783,23.768800735473633],[0.0,7.52370023727417,35.309600830078125]],"101-Gun-5-C":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/101-Gun-5-C.stl",[-1.8524999618530273,-8.314800262451172,-7.009099960327148],[2.5738000869750977,13.56779956817627,7.411799907684326]],"102-Arm-6-R-B":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Arms/102-Arm-6-R-B.stl",[-7.142000198364258,-2.998199939727783,23.450599670410156],[0.8772000074386597,8.40839958190918,35.30950164794922]],"102-Gun-5-D":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/102-Gun-5-D.stl",[-1.7422000169754028,-8.339200019836426,-6.096799850463867],[2.573499917984009,13.543399810791016,7.633200168609619]],"103-Gun-5-E":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/103-Gun-5-E.stl",[-1.8524999618530273,-8.314800262451172,-6.096799850463867],[2.5738000869750977,13.567700386047363,7.411799907684326]],"104-Gun-5-F":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/104-Gun-5-F.stl",[-2.0660998821258545,-8.31470012664795,-6.09689998626709],[3.5295000076293945,13.56779956817627,5.221499919891357]],"105-Gun-5-G":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/105-Gun-5-G.stl",[-2.0660998821258545,-8.314800262451172,-6.096799850463867],[3.529599905014038,13.567700386047363,7.383600234985352]],"106-Arm-7-R-A":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Arms/106-Arm-7-R-A.stl",[-6.9120001792907715,-3.709199905395508,23.131500244140625],[3.2318999767303467,4.0366997718811035,36.31829833984375]],"106-Axe-3-A-Bionic":["Mar Fil - Tacticus/VeteranBladeSquad","VeteranBladeSquad/VeteranBladeSquad/Melee/Melee-RawSTL/Axes/106-Axe-3-A-Bionic.stl",[-2.4321999549865723,-7.282199859619141,-18.444400787353516],[2.3015999794006348,5.777500152587891,30.653600692749023]],"106-Gun-5-H":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/106-Gun-5-H.stl",[-1.601699948310852,-8.31470012664795,-6.97189998626709],[4.3343000411987305,13.567700386047363,5.22130012512207]],"107-Arm-7-R-B":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Arms/107-Arm-7-R-B.stl",[-6.912099838256836,-3.8854000568389893,23.06679916381836],[4.5015997886657715,4.0366997718811035,36.31829833984375]],"107-Gun-5-I":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/107-Gun-5-I.stl",[-1.8588000535964966,-8.314800262451172,-6.97189998626709],[4.334099769592285,13.567700386047363,7.412199974060059]],"108-Axe-3-B-Bionic":["Mar Fil - Tacticus/VeteranBladeSquad","VeteranBladeSquad/VeteranBladeSquad/Melee/Melee-RawSTL/Axes/108-Axe-3-B-Bionic.stl",[-2.5478999614715576,-7.282199859619141,-18.444599151611328],[2.3015999794006348,5.777500152587891,30.653600692749023]],"108-CombiWeapon-1-A":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/108-CombiWeapon-1-A.stl",[-16.349199295043945,-2.618000030517578,23.943199157714844],[12.110199928283691,19.065099716186523,36.02939987182617]],"109-CombiWeapon-1-B":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/109-CombiWeapon-1-B.stl",[-16.118999481201172,-2.493299961090088,23.828399658203125],[12.24530029296875,18.957799911499023,36.02920150756836]],"110-CombiWeapon-1-C":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/110-CombiWeapon-1-C.stl",[-17.896799087524414,-2.488800048828125,23.296199798583984],[12.264900207519531,19.990299224853516,35.14339828491211]],"111-Arm-8-R-A":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Arms/111-Arm-8-R-A.stl",[-6.635499954223633,-2.741499900817871,23.965299606323242],[-0.14730000495910645,6.492700099945068,35.863800048828125]],"111-CombiWeapon-2-A":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/111-CombiWeapon-2-A.stl",[-12.329000473022461,-2.5539000034332275,22.177400588989258],[12.77929973602295,21.393400192260742,35.31909942626953]],"112-Arm-8-R-B":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Arms/112-Arm-8-R-B.stl",[-6.635700225830078,-2.741499900817871,23.316499710083008],[0.7347999811172485,7.346199989318848,35.863800048828125]],"112-CombiWeapon-2-B":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/112-CombiWeapon-2-B.stl",[-12.072099685668945,-2.761199951171875,21.898700714111328],[12.532299995422363,21.195600509643555,35.44710159301758]],"113-CombiWeapon-2-C":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/113-CombiWeapon-2-C.stl",[-13.731300354003906,-2.6868999004364014,21.627399444580078],[12.50979995727539,22.539499282836914,34.97959899902344]],"114-CombiWeapon-3-A":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/114-CombiWeapon-3-A.stl",[-18.478900909423828,-2.7602999210357666,20.64940071105957],[11.223199844360352,17.466299057006836,34.767398834228516]],"115-CombiWeapon-3-B":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/115-CombiWeapon-3-B.stl",[-18.251800537109375,-2.7623000144958496,18.62649917602539],[11.223899841308594,17.374799728393555,34.76380157470703]],"116-CombiWeapon-3-C":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/116-CombiWeapon-3-C.stl",[-20.028099060058594,-2.7618000507354736,20.05900001525879],[11.21560001373291,18.297000885009766,34.76559829711914]],"117-Arm-9-R-B":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Arms/117-Arm-9-R-B.stl",[-6.6203999519348145,-2.570499897003174,23.858600616455078],[0.7263000011444092,9.059000015258789,35.79819869995117]],"117-CombiWeapon-4-A":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/117-CombiWeapon-4-A.stl",[-14.506199836730957,-2.2267000675201416,-6.835400104522705],[10.056099891662598,3.229300022125244,5.13539981842041]],"118-CombiWeapon-4-B":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/118-CombiWeapon-4-B.stl",[-14.503700256347656,-2.605600118637085,-6.920100212097168],[10.056099891662598,3.228800058364868,4.774600028991699]],"119-CombiWeapon-4-C":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/119-CombiWeapon-4-C.stl",[-16.143699645996094,-1.8705999851226807,-7.249800205230713],[10.056099891662598,3.3178000450134277,4.6280999183654785]],"120-Pistol":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/120-Pistol.stl",[-12.447600364685059,-1.6203999519348145,-2.741300106048584],[0.4652000069618225,2.409600019454956,5.837900161743164]],"121-Arm-10-R-A":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Arms/121-Arm-10-R-A.stl",[-6.162099838256836,-2.726900100708008,22.55430030822754],[0.9253000020980835,7.610899925231934,36.20669937133789]],"122-Arm-10-R-B":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Arms/122-Arm-10-R-B.stl",[-6.161499977111816,-2.726799964904785,22.473499298095703],[1.4222999811172485,9.01710033416748,36.20669937133789]],"126-Arm-11-R-A":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Arms/126-Arm-11-R-A.stl",[5.263599872589111,-3.418299913406372,27.779800415039062],[14.899399757385254,9.764399528503418,35.79710006713867]],"127-Arm-11-R-B":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Arms/127-Arm-11-R-B.stl",[5.263599872589111,-3.418299913406372,27.345600128173828],[16.202800750732422,9.764399528503418,35.797000885009766]],"131-Arm-12-R-A":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Arms/131-Arm-12-R-A.stl",[5.06689977645874,-3.323199987411499,26.912200927734375],[17.78059959411621,2.9867000579833984,36.65039825439453]],"132-Arm-12-R-B":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Arms/132-Arm-12-R-B.stl",[5.0665998458862305,-4.086900234222412,26.7544002532959],[18.641000747680664,2.9867000579833984,36.6505012512207]],"145-PowerAxe-1-1-B":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/TwoHandedWeapons/145-PowerAxe-1-1-B.stl",[-12.551400184631348,-2.8959999084472656,22.319400787353516],[32.38140106201172,18.58289909362793,43.170501708984375]],"147-PowerAxe-1-2-B":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/TwoHandedWeapons/147-PowerAxe-1-2-B.stl",[-16.365400314331055,-2.8959999084472656,20.207199096679688],[23.33169937133789,18.572099685668945,37.555999755859375]],"149-PowerAxe-2-1-B":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/TwoHandedWeapons/149-PowerAxe-2-1-B.stl",[-10.653599739074707,-11.148099899291992,13.905200004577637],[37.01689910888672,14.363900184631348,35.08039855957031]],"151-PowerAxe-2-2-B":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/TwoHandedWeapons/151-PowerAxe-2-2-B.stl",[-10.653599739074707,-5.896299839019775,14.23740005493164],[35.99549865722656,13.113300323486328,35.08039855957031]],"153-PowerHammer-1-B":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/TwoHandedWeapons/153-PowerHammer-1-B.stl",[-10.653599739074707,-10.29419994354248,14.992899894714355],[34.41529846191406,14.116600036621094,35.080501556396484]],"155-PowerHammer-2-B":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/TwoHandedWeapons/155-PowerHammer-2-B.stl",[-10.07610034942627,-3.8215999603271484,14.058600425720215],[24.28730010986328,16.830400466918945,45.24959945678711]],"157-PowerSpear-1-B":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/TwoHandedWeapons/157-PowerSpear-1-B.stl",[-10.65369987487793,-8.414600372314453,17.429800033569336],[41.148101806640625,16.20050048828125,35.08039855957031]],"159-PowerSpear-2-B":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/TwoHandedWeapons/159-PowerSpear-2-B.stl",[-10.076000213623047,-3.822000026702881,12.25409984588623],[31.315200805664062,12.240099906921387,52.42839813232422]],"175-ChainSword-1-R":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Melee/175-ChainSword-1-R.stl",[-2.4530999660491943,-2.3499999046325684,-3.786799907684326],[1.853700041770935,2.9672000408172607,26.45050048828125]],"175-ChainSword-1-R.001":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Melee/175-ChainSword-1-R.stl",[-2.4530999660491943,-2.3499999046325684,-3.786799907684326],[1.853700041770935,2.9672000408172607,26.45050048828125]],"176-ChainSword-2-R.001":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Melee/176-ChainSword-2-R.stl",[-2.6224000453948975,-15.756799697875977,-4.154200077056885],[1.6397000551223755,3.5037999153137207,20.880300521850586]],"177-ChainSword-3-R.001":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Melee/177-ChainSword-3-R.stl",[-2.624300003051758,-22.282800674438477,-2.5824999809265137],[1.840999960899353,5.206299781799316,11.66450023651123]],"178-CombatKnife-1-R":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Melee/178-CombatKnife-1-R.stl",[-2.7197999954223633,-2.0429000854492188,-2.5246999263763428],[1.069200038909912,2.9911000728607178,17.546499252319336]],"179-CombatKnife-2-R":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Melee/179-CombatKnife-2-R.stl",[-2.720599889755249,-1.3543000221252441,-15.744500160217285],[1.0455000400543213,2.994999885559082,4.3282999992370605]],"180-CombatKnife-3-R":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Melee/180-CombatKnife-3-R.stl",[-2.4902000427246094,-14.066499710083008,-2.601900100708008],[1.3933000564575195,4.4710001945495605,6.748199939727783]],"181-Esvicerator-1-R":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Melee/181-Esvicerator-1-R.stl",[-2.7107999324798584,-4.890200138092041,-6.858799934387207],[2.6805999279022217,3.526599884033203,35.05889892578125]],"182-Esvicerator-2-R":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Melee/182-Esvicerator-2-R.stl",[-2.6038999557495117,-21.21179962158203,-6.385499954223633],[2.648200035095215,5.53380012512207,27.97100067138672]],"183-Esvicerator-3-R":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Melee/183-Esvicerator-3-R.stl",[-4.306300163269043,-30.423099517822266,-3.9528000354766846],[2.0773000717163086,8.057100296020508,15.203800201416016]],"185-PowerAxe-A-2-R":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Melee/185-PowerAxe-A-2-R.stl",[-2.603800058364868,-18.355199813842773,-4.575300216674805],[1.5708999633789062,3.9096999168395996,18.258800506591797]],"186-PowerAxe-A-3-R":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Melee/186-PowerAxe-A-3-R.stl",[-2.572000026702881,-21.763099670410156,-2.622299909591675],[1.5740000009536743,5.212900161743164,12.121399879455566]],"187-PowerAxe-B-1-R":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Melee/187-PowerAxe-B-1-R.stl",[-2.707900047302246,-11.071800231933594,-18.876699447631836],[1.7608000040054321,7.42080020904541,26.33989906311035]],"188-PowerAxe-B-2-R":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Melee/188-PowerAxe-B-2-R.stl",[-2.6040000915527344,-23.885099411010742,-15.566399574279785],[1.7608000040054321,12.201299667358398,24.885400772094727]],"189-PowerAxe-B-3-R":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Melee/189-PowerAxe-B-3-R.stl",[-2.5058000087738037,-21.061899185180664,-10.98449993133545],[3.0908000469207764,24.44420051574707,14.665800094604492]],"190-PowerAxe-C-1-R":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Melee/190-PowerAxe-C-1-R.stl",[-2.707900047302246,-9.435099601745605,-13.601900100708008],[1.7228000164031982,2.9639999866485596,26.518800735473633]],"191-PowerAxe-C-2-R":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Melee/191-PowerAxe-C-2-R.stl",[-2.6040000915527344,-23.16830062866211,-10.93340015411377],[1.7228000164031982,9.049500465393066,21.50309944152832]],"192-PowerAxe-C-3-R":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Melee/192-PowerAxe-C-3-R.stl",[-2.650599956512451,-14.346699714660645,-16.101999282836914],[3.9730000495910645,24.457500457763672,7.082499980926514]],"193-PowerHammer-A-1-R":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Melee/193-PowerHammer-A-1-R.stl",[-2.7597999572753906,-7.135799884796143,-7.504499912261963],[2.319499969482422,7.135799884796143,19.54210090637207]],"194-PowerHammer-A-2-R":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Melee/194-PowerHammer-A-2-R.stl",[-2.6040000915527344,-16.291400909423828,-6.0903000831604],[2.539599895477295,5.058199882507324,18.826000213623047]],"196-PowerHammer-B-1-R":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Melee/196-PowerHammer-B-1-R.stl",[-3.3870999813079834,-7.432499885559082,-15.647199630737305],[3.000999927520752,6.926499843597412,27.095199584960938]],"198-PowerHammer-B-3-R":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Melee/198-PowerHammer-B-3-R.stl",[-4.90369987487793,-26.222400665283203,-6.926799774169922],[2.416100025177002,14.241700172424316,17.770299911499023]],"2":["_Unsorted/Mar Fil/HelmetsUpdate","HelmetsUpdate/HelmetsUpdates/HelmetsUpdates-1/2.stl",[-2.3570001125335693,-3.629199981689453,33.122798919677734],[6.27869987487793,3.629199981689453,41.666900634765625]],"2-Helmet-B":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Helmets/Helmet-RawStl/2-Helmet-B.stl",[-3.5813000202178955,-3.447700023651123,-2.719099998474121],[4.622600078582764,3.4475998878479004,5.397799968719482]],"2.002":["_Unsorted/Mar Fil/HelmetsUpdate","HelmetsUpdate/HelmetsUpdates/HelmetsUpdates/2.stl",[-2.3570001125335693,-3.6291000843048096,33.122798919677734],[6.278800010681152,3.629199981689453,41.66640090942383]],"202-PowerSword-A-1-R":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Melee/202-PowerSword-A-1-R.stl",[-2.723599910736084,-4.547100067138672,-5.151500225067139],[1.6053999662399292,4.547100067138672,32.58190155029297]],"205-PowerSword-B-1-R":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Melee/205-PowerSword-B-1-R.stl",[-2.7385001182556152,-3.802000045776367,-4.937699794769287],[1.9055999517440796,3.802500009536743,31.340099334716797]],"208-PowerSword-C-1-R":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Melee/208-PowerSword-C-1-R.stl",[-2.729599952697754,-3.8041999340057373,-7.744699954986572],[1.6079000234603882,3.803100109100342,37.28350067138672]],"209-PowerSword-C-2-R":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Melee/209-PowerSword-C-2-R.stl",[-2.6040000915527344,-22.560400009155273,-6.841800212860107],[1.8533999919891357,6.110400199890137,28.786699295043945]],"210-PowerSword-C-3-R":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Melee/210-PowerSword-C-3-R.stl",[-2.792099952697754,-31.241199493408203,-5.151599884033203],[1.7008999586105347,8.548999786376953,17.063899993896484]],"211-BoltPistol-R":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Pistols/211-BoltPistol-R.stl",[-2.707900047302246,-10.315099716186523,-1.5068999528884888],[1.3938000202178955,2.9639999866485596,7.072400093078613]],"211-Shield-R":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Melee/211-Shield-R.stl",[-8.329099655151367,-5.638299942016602,-12.54069995880127],[8.333600044250488,3.178299903869629,8.254599571228027]],"212-HeavyBoltPistol-R":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Pistols/212-HeavyBoltPistol-R.stl",[-2.707900047302246,-14.531399726867676,-1.469499945640564],[1.3938000202178955,2.9639999866485596,7.718100070953369]],"213-PlasmaPistol-R":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Pistols/213-PlasmaPistol-R.stl",[-2.707900047302246,-13.829299926757812,-1.0716999769210815],[1.7856999635696411,3.0343000888824463,8.03950023651123]],"214-VolkitePistol-R":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Pistols/214-VolkitePistol-R.stl",[-2.707900047302246,-16.2278995513916,-1.5003000497817993],[1.607699990272522,2.9639999866485596,7.126800060272217]],"23-Torso-2":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Chest/23-Torso-2.stl",[-5.8734002113342285,-5.635700225830078,25.51180076599121],[5.873199939727783,7.328499794006348,37.10210037231445]],"23-Torso-2.001":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Chest/23-Torso-2.stl",[-5.8734002113342285,-5.635700225830078,25.51180076599121],[5.873199939727783,7.328499794006348,37.10210037231445]],"25-StormBolter":["Mar Fil - Terminator/CaptainTerminator","CaptainTerminator/CaptainTerminator/RawStlCaptainTerminator/25-StormBolter.stl",[-4.950900077819824,-16.965999603271484,-6.141200065612793],[6.797100067138672,0.6237999796867371,8.951899528503418]],"26-CombiWeaponMelta":["Mar Fil - Terminator/CaptainTerminator","CaptainTerminator/CaptainTerminator/RawStlCaptainTerminator/26-CombiWeaponMelta.stl",[-2.9944000244140625,-23.779600143432617,-3.9017999172210693],[3.144399881362915,0.6227999925613403,9.161499977111816]],"27-CombiWeaponFlamer":["Mar Fil - Terminator/CaptainTerminator","CaptainTerminator/CaptainTerminator/RawStlCaptainTerminator/27-CombiWeaponFlamer.stl",[-2.5943000316619873,-21.51930046081543,-4.127500057220459],[3.9261999130249023,0.6227999925613403,9.448399543762207]],"28-CombiWeaponPlasma":["Mar Fil - Terminator/CaptainTerminator","CaptainTerminator/CaptainTerminator/RawStlCaptainTerminator/28-CombiWeaponPlasma.stl",[-2.8645999431610107,-23.77739906311035,-4.515999794006348],[3.232100009918213,0.6226999759674072,9.44849967956543]],"28-Legs-1":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Legs/28-Legs-1.stl",[-9.862899780273438,-13.696399688720703,2.1110000610351562],[8.390800476074219,7.442800045013428,29.586599349975586]],"29-Legs-2":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Legs/29-Legs-2.stl",[-8.74530029296875,-11.68239974975586,-0.02319999970495701],[9.121500015258789,9.715700149536133,26.886899948120117]],"3-Helmet-2-A":["Mar Fil - Tacticus/VeteranBladeSquad","VeteranBladeSquad/VeteranBladeSquad/Helmets/Helmets-RawSTL/3-Helmet-2-A.stl",[-3.5792999267578125,-3.4458000659942627,-2.717600107192993],[4.594399929046631,3.44569993019104,5.395199775695801]],"30-Legs-3":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Legs/30-Legs-3.stl",[-11.808600425720215,-6.345600128173828,-0.0723000019788742],[12.172100067138672,8.537599563598633,27.35580062866211]],"31-Legs-4":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Legs/31-Legs-4.stl",[-5.940999984741211,-13.01830005645752,0.3398999869823456],[11.661999702453613,8.729499816894531,27.79960060119629]],"32-Legs-5":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Legs/32-Legs-5.stl",[-9.937000274658203,-11.998600006103516,1.9178999662399292],[8.09280014038086,9.156900405883789,29.57469940185547]],"33-Legs-1-A":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Legs(JumpPack)/33-Legs-1-A.stl",[-7.542900085449219,-10.263199806213379,9.472599983215332],[13.51669979095459,8.336600303649902,39.88100051879883]],"34-Legs-1-B":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Legs(JumpPack)/34-Legs-1-B.stl",[-7.541399955749512,-10.263099670410156,9.472599983215332],[13.51669979095459,8.336600303649902,39.88100051879883]],"34-Legs-1-B.001":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Legs(JumpPack)/34-Legs-1-B.stl",[-7.541399955749512,-10.263099670410156,9.472599983215332],[13.51669979095459,8.336600303649902,39.88100051879883]],"35-Legs-2-A":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Legs(JumpPack)/35-Legs-2-A.stl",[-8.417699813842773,-7.540500164031982,5.896100044250488],[12.274100303649902,11.524399757385254,36.21049880981445]],"36-Legs-2-B":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Legs(JumpPack)/36-Legs-2-B.stl",[-8.417699813842773,-7.540500164031982,5.896100044250488],[12.274100303649902,11.524399757385254,36.21049880981445]],"37-Arm-1-B":["Mar Fil - Tacticus/VeteranBladeSquad","VeteranBladeSquad/VeteranBladeSquad/Arms/Arms-RawSTL/37-Arm-1-B.stl",[5.46560001373291,-2.6784000396728516,25.43600082397461],[13.455900192260742,7.756100177764893,35.45539855957031]],"37-Legs-3-A":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Legs(JumpPack)/37-Legs-3-A.stl",[-13.72599983215332,-7.865200042724609,6.530099868774414],[9.69219970703125,11.20110034942627,35.093101501464844]],"38-Legs-3-B":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Legs(JumpPack)/38-Legs-3-B.stl",[-13.72599983215332,-7.865300178527832,6.53000020980835],[9.691399574279785,11.199999809265137,35.09260177612305]],"39-Arm-2-B":["Mar Fil - Tacticus/VeteranBladeSquad","VeteranBladeSquad/VeteranBladeSquad/Arms/Arms-RawSTL/39-Arm-2-B.stl",[5.467199802398682,-2.7342000007629395,23.782800674438477],[10.881500244140625,6.526899814605713,34.292198181152344]],"39-Legs-4-A":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Legs(JumpPack)/39-Legs-4-A.stl",[-13.697799682617188,-7.039100170135498,7.6072998046875],[9.383000373840332,12.50059986114502,37.32080078125]],"4":["_Unsorted/Mar Fil/HelmetsUpdate","HelmetsUpdate/HelmetsUpdates/HelmetsUpdates-1/4.stl",[-2.3570001125335693,-3.629199981689453,33.122798919677734],[6.293799877166748,3.629199981689453,41.66680145263672]],"4-Helmet-4":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Helmet-Heads/4-Helmet-4.stl",[-2.3568999767303467,-3.629300117492676,33.12289810180664],[6.2779998779296875,3.6287999153137207,41.666500091552734]],"4-Helmet-D":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Helmets/Helmet-RawStl/4-Helmet-D.stl",[-3.5804998874664307,-3.447700023651123,-2.7183001041412354],[4.621099948883057,3.447700023651123,5.39739990234375]],"4.001":["_Unsorted/Mar Fil/HelmetsUpdate","HelmetsUpdate/HelmetsUpdates/HelmetsUpdates/4.stl",[-2.83870005607605,-3.629199981689453,33.122798919677734],[6.278800010681152,3.629300117492676,45.981300354003906]],"40-Legs-4-B":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Legs(JumpPack)/40-Legs-4-B.stl",[-13.697799682617188,-7.040599822998047,7.6072001457214355],[9.383000373840332,12.50059986114502,37.32080078125]],"41-Arm-3-B":["Mar Fil - Tacticus/VeteranBladeSquad","VeteranBladeSquad/VeteranBladeSquad/Arms/Arms-RawSTL/41-Arm-3-B.stl",[5.466100215911865,-3.271899938583374,27.384300231933594],[17.0231990814209,7.1971001625061035,35.10260009765625]],"41-Legs-5-A":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Legs(JumpPack)/41-Legs-5-A.stl",[-7.722099781036377,-9.210100173950195,3.0732998847961426],[12.333200454711914,6.741399765014648,33.7510986328125]],"42-Legs-5-B":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Legs(JumpPack)/42-Legs-5-B.stl",[-8.152299880981445,-9.209400177001953,3.0741000175476074],[12.333100318908691,6.7393999099731445,33.7510986328125]],"43-Arm-4-B":["Mar Fil - Tacticus/VeteranBladeSquad","VeteranBladeSquad/VeteranBladeSquad/Arms/Arms-RawSTL/43-Arm-4-B.stl",[5.466000080108643,-4.372300148010254,23.220800399780273],[12.873900413513184,4.499899864196777,35.60860061645508]],"43-Legs-6-A":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Legs(JumpPack)/43-Legs-6-A.stl",[-12.137800216674805,-12.995599746704102,1.7336000204086304],[7.709199905395508,11.311800003051758,28.24090003967285]],"44-Legs-6-B":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Legs(JumpPack)/44-Legs-6-B.stl",[-12.13700008392334,-12.994199752807617,1.7336000204086304],[7.7093000411987305,11.311800003051758,28.24090003967285]],"45-Arm-5-B":["Mar Fil - Tacticus/VeteranBladeSquad","VeteranBladeSquad/VeteranBladeSquad/Arms/Arms-RawSTL/45-Arm-5-B.stl",[3.8529000282287598,-2.4195001125335693,26.617799758911133],[12.476699829101562,9.24940013885498,34.69029998779297]],"45-Legs-7-A":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Legs(JumpPack)/45-Legs-7-A.stl",[-9.889399528503418,-5.695700168609619,-0.03240000084042549],[11.036499977111816,8.214300155639648,29.41990089416504]],"46-Legs-7-B":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Legs(JumpPack)/46-Legs-7-B.stl",[-9.890600204467773,-5.6956000328063965,-0.032499998807907104],[11.038200378417969,8.214500427246094,29.41939926147461]],"47-Arm-6-B":["Mar Fil - Tacticus/VeteranBladeSquad","VeteranBladeSquad/VeteranBladeSquad/Arms/Arms-RawSTL/47-Arm-6-B.stl",[5.4664998054504395,-4.436100006103516,21.717500686645508],[14.728500366210938,3.2355000972747803,35.152400970458984]],"47-Legs-8-A":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Legs(JumpPack)/47-Legs-8-A.stl",[-6.492000102996826,-10.542099952697754,5.112500190734863],[11.51669979095459,9.012200355529785,35.65999984741211]],"48-Legs-8-B":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Legs(JumpPack)/48-Legs-8-B.stl",[-7.053199768066406,-10.543600082397461,5.112500190734863],[11.515600204467773,9.012200355529785,35.65959930419922]],"49-Arm-7-B":["Mar Fil - Tacticus/VeteranBladeSquad","VeteranBladeSquad/VeteranBladeSquad/Arms/Arms-RawSTL/49-Arm-7-B.stl",[4.698800086975098,-5.136499881744385,28.545700073242188],[17.017099380493164,3.1333000659942627,37.61009979248047]],"5":["_Unsorted/Mar Fil/HelmetsUpdate","HelmetsUpdate/HelmetsUpdates/HelmetsUpdates/5.stl",[-2.3570001125335693,-3.629199981689453,33.122798919677734],[6.251999855041504,3.6291000843048096,41.667198181152344]],"5-Helmet-3-A":["Mar Fil - Tacticus/VeteranBladeSquad","VeteranBladeSquad/VeteranBladeSquad/Helmets/Helmets-RawSTL/5-Helmet-3-A.stl",[-3.5792999267578125,-3.44569993019104,-2.717600107192993],[4.713099956512451,3.4458000659942627,6.031499862670898]],"5-Helmet-E":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Helmets/Helmet-RawStl/5-Helmet-E.stl",[-3.5804998874664307,-3.447700023651123,-2.7183001041412354],[4.888800144195557,3.447700023651123,5.39739990234375]],"51-Arm-8-B":["Mar Fil - Tacticus/VeteranBladeSquad","VeteranBladeSquad/VeteranBladeSquad/Arms/Arms-RawSTL/51-Arm-8-B.stl",[5.466100215911865,-3.163800001144409,28.134599685668945],[16.851699829101562,4.769599914550781,36.30009841918945]],"53-Arm-9-B":["Mar Fil - Tacticus/VeteranBladeSquad","VeteranBladeSquad/VeteranBladeSquad/Arms/Arms-RawSTL/53-Arm-9-B.stl",[5.466100215911865,-5.453800201416016,21.777799606323242],[14.388699531555176,3.0947999954223633,35.17879867553711]],"55-Arm-10-B":["Mar Fil - Tacticus/VeteranBladeSquad","VeteranBladeSquad/VeteranBladeSquad/Arms/Arms-RawSTL/55-Arm-10-B.stl",[5.332799911499023,-3.5009000301361084,28.12350082397461],[15.910400390625,5.903299808502197,35.7848014831543]],"55-JumpPack-1":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/JumpPacks/55-JumpPack-1.stl",[-14.161100387573242,-14.597399711608887,25.26650047302246],[14.161800384521484,-3.5736000537872314,43.84320068359375]],"6":["_Unsorted/Mar Fil/HelmetsUpdate","HelmetsUpdate/HelmetsUpdates/HelmetsUpdates-1/6.stl",[-2.3570001125335693,-3.6291000843048096,33.122798919677734],[6.399099826812744,3.6291000843048096,41.66680145263672]],"6-Helmet-3-B":["Mar Fil - Tacticus/VeteranBladeSquad","VeteranBladeSquad/VeteranBladeSquad/Helmets/Helmets-RawSTL/6-Helmet-3-B.stl",[-3.746500015258789,-3.924499988555908,-2.717400074005127],[4.712800025939941,3.740799903869629,6.031300067901611]],"6.001":["_Unsorted/Mar Fil/HelmetsUpdate","HelmetsUpdate/HelmetsUpdates/HelmetsUpdates/6.stl",[-2.3570001125335693,-3.629199981689453,33.122798919677734],[6.376999855041504,3.6291000843048096,42.33769989013672]],"7":["_Unsorted/Mar Fil/HelmetsUpdate","HelmetsUpdate/HelmetsUpdates/HelmetsUpdates-1/7.stl",[-2.3570001125335693,-3.629199981689453,33.122798919677734],[6.278900146484375,3.6291000843048096,41.66680145263672]],"70-Gun-1-A":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/70-Gun-1-A.stl",[-14.520000457763672,-2.7372000217437744,23.062000274658203],[11.57289981842041,19.73940086364746,37.741798400878906]],"71-Gun-1-B":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/71-Gun-1-B.stl",[-14.519200325012207,-2.7372000217437744,23.064699172973633],[11.57289981842041,19.739500045776367,37.742000579833984]],"72-Gun-1-C":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/72-Gun-1-C.stl",[-14.519200325012207,-2.7370998859405518,23.06209945678711],[11.572799682617188,19.739500045776367,37.52880096435547]],"73-Gun-1-D":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/73-Gun-1-D.stl",[-14.498200416564941,-2.737499952316284,24.353700637817383],[11.573100090026855,19.72719955444336,37.74209976196289]],"74-Gun-1-E":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/74-Gun-1-E.stl",[-14.519200325012207,-2.7370998859405518,24.351999282836914],[11.572799682617188,19.739500045776367,37.52880096435547]],"75-Gun-1-F":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/75-Gun-1-F.stl",[-14.520000457763672,-2.7370998859405518,24.017000198364258],[11.57289981842041,19.739500045776367,35.407798767089844]],"76-Arm-1-R-A":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Arms/76-Arm-1-R-A.stl",[-5.213900089263916,-7.607100009918213,24.77280044555664],[5.449900150299072,3.488100051879883,36.386600494384766]],"76-Gun-1-G":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/76-Gun-1-G.stl",[-14.519200325012207,-2.7370998859405518,24.01689910888672],[11.57289981842041,19.739500045776367,37.479400634765625]],"77-Arm-1-R-B":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Arms/77-Arm-1-R-B.stl",[-5.213900089263916,-8.057999610900879,24.77280044555664],[6.6585001945495605,3.488100051879883,36.38669967651367]],"77-Gun-1-H":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/77-Gun-1-H.stl",[-14.519700050354004,-2.7370998859405518,23.029499053955078],[11.572799682617188,19.739500045776367,35.407798767089844]],"78-Gun-1-I":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/78-Gun-1-I.stl",[-14.519200325012207,-2.7372000217437744,23.029399871826172],[11.572799682617188,19.739500045776367,37.519798278808594]],"79-Gun-2-A":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/79-Gun-2-A.stl",[-10.64900016784668,-2.7432000637054443,21.219100952148438],[12.84689998626709,20.102500915527344,35.89680099487305]],"8":["_Unsorted/Mar Fil/HelmetsUpdate","HelmetsUpdate/HelmetsUpdates/HelmetsUpdates/8.stl",[-2.198499917984009,-3.629199981689453,33.122798919677734],[7.828499794006348,3.629199981689453,41.667198181152344]],"8-Helmet-8":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Helmet-Heads/8-Helmet-8.stl",[-2.3396999835968018,-3.6226000785827637,33.12710189819336],[6.103700160980225,3.6226999759674072,41.64799880981445]],"80-Gun-2-B":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/80-Gun-2-B.stl",[-10.65060043334961,-2.7421000003814697,21.2189998626709],[12.84850025177002,20.099700927734375,35.897098541259766]],"81-Arm-2-R-A":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Arms/81-Arm-2-R-A.stl",[-6.416100025177002,-2.8812999725341797,22.398500442504883],[3.7483999729156494,3.7111001014709473,36.47380065917969]],"81-Gun-2-C":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/81-Gun-2-C.stl",[-10.65060043334961,-2.7421000003814697,21.21929931640625],[12.84689998626709,20.099700927734375,35.68510055541992]],"82-Arm-2-R-B":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Arms/82-Arm-2-R-B.stl",[-6.416100025177002,-3.234100103378296,22.398399353027344],[5.15500020980835,3.7109999656677246,36.47380065917969]],"82-Gun-2-D":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/82-Gun-2-D.stl",[-10.631400108337402,-2.7458999156951904,22.507699966430664],[12.847399711608887,20.084699630737305,35.898101806640625]],"83-Gun-2-E":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/83-Gun-2-E.stl",[-10.65060043334961,-2.7430999279022217,22.50790023803711],[12.846400260925293,20.097700119018555,35.68510055541992]],"84-Gun-2-F":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/84-Gun-2-F.stl",[-10.648200035095215,-2.7430999279022217,22.141799926757812],[12.846799850463867,20.098499298095703,35.55459976196289]],"85-Gun-2-G":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/85-Gun-2-G.stl",[-10.65060043334961,-2.7432000637054443,22.141799926757812],[12.846400260925293,20.097700119018555,35.634300231933594]],"86-Arm-3-R-A":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Arms/86-Arm-3-R-A.stl",[-9.0108003616333,-4.138400077819824,29.619400024414062],[3.400700092315674,6.633999824523926,38.10929870605469]],"86-Gun-2-H":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/86-Gun-2-H.stl",[-10.647600173950195,-2.7430999279022217,21.12689971923828],[12.846400260925293,20.098499298095703,35.55459976196289]],"87-ARm-3-R-B":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Arms/87-ARm-3-R-B.stl",[-9.0108003616333,-4.138400077819824,29.619400024414062],[3.9983999729156494,6.633999824523926,38.81039810180664]],"87-Gun-2-I":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/87-Gun-2-I.stl",[-10.65060043334961,-2.7421000003814697,21.12700080871582],[12.846400260925293,20.097700119018555,35.677398681640625]],"88-Gun-3-A":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/88-Gun-3-A.stl",[-15.886799812316895,-3.2370998859405518,19.311500549316406],[11.38700008392334,16.620800018310547,35.24959945678711]],"89-Gun-3-B":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/89-Gun-3-B.stl",[-15.886500358581543,-3.2370998859405518,19.312299728393555],[11.38700008392334,16.620100021362305,35.248199462890625]],"9":["_Unsorted/Mar Fil/HelmetsUpdate","HelmetsUpdate/HelmetsUpdates/HelmetsUpdates/9.stl",[-2.1984000205993652,-3.629300117492676,33.12289810180664],[7.827499866485596,3.6291000843048096,41.667198181152344]],"90-Gun-3-C":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/90-Gun-3-C.stl",[-15.88640022277832,-3.2370998859405518,19.31209945678711],[11.38700008392334,16.62019920349121,35.3577995300293]],"91-Arm-4-R-A":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Arms/91-Arm-4-R-A.stl",[-6.666399955749512,-2.7922000885009766,23.15019989013672],[1.3401999473571777,7.904200077056885,36.01559829711914]],"91-Gun-3-D":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/91-Gun-3-D.stl",[-15.865900039672852,-3.236799955368042,19.322599411010742],[11.38700008392334,16.61210060119629,35.25040054321289]],"92-Arm-4-R-B":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Arms/92-Arm-4-R-B.stl",[-6.666399955749512,-2.7922000885009766,23.149999618530273],[1.9458999633789062,8.758999824523926,36.015201568603516]],"92-Gun-3-E":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/92-Gun-3-E.stl",[-15.887499809265137,-3.2370998859405518,19.311899185180664],[11.38700008392334,16.62030029296875,35.357601165771484]],"93-Gun-3-F":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/93-Gun-3-F.stl",[-15.886799812316895,-3.2370998859405518,19.311899185180664],[11.38700008392334,16.61870002746582,35.117401123046875]],"94-Gun-3-G":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/94-Gun-3-G.stl",[-15.88759994506836,-3.2370998859405518,19.311899185180664],[11.38700008392334,16.62030029296875,35.117000579833984]],"95-Gun-3-H":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/95-Gun-3-H.stl",[-15.887499809265137,-3.2370998859405518,19.311899185180664],[11.38700008392334,16.61870002746582,35.117000579833984]],"96-Arm-5-R-A":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Arms/96-Arm-5-R-A.stl",[-6.75600004196167,-3.099299907684326,24.90060043334961],[-0.07209999859333038,8.794300079345703,35.2411003112793]],"96-Gun-3-I":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/96-Gun-3-I.stl",[-15.887499809265137,-3.2370998859405518,19.311899185180664],[11.38700008392334,16.62030029296875,35.30270004272461]],"97-Arm-5-R-B":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Arms/97-Arm-5-R-B.stl",[-6.756100177764893,-3.099299907684326,24.547500610351562],[0.4756999909877777,10.265199661254883,35.2411994934082]],"97-Gun-4-A":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/97-Gun-4-A.stl",[5.466000080108643,-2.2987000942230225,20.880300521850586],[13.813199996948242,16.583200454711914,43.67070007324219]],"98-Gun-4-B":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/98-Gun-4-B.stl",[5.4653000831604,-2.2990000247955322,20.880399703979492],[14.361100196838379,16.910200119018555,43.67060089111328]],"99-Gun-5-A":["Mar Fil - Tacticus/VeteranSquad","VeteranSquad/VeteranSquad/Weapons/Weapons-RawSTL/99-Gun-5-A.stl",[-1.7421000003814697,-8.31470012664795,-7.008999824523926],[3.4656999111175537,13.567700386047363,7.6321001052856445]],"116-Arm-9-R-A":["Mar Fil - Tacticus/AssaultMarines-V2","AssaultMarines-V2/AssaultMarines-V2/RawSTL/Arms/116-Arm-9-R-A.stl",[-6.6204,-2.5705,24.1234],[0.4503,7.6652,35.798]]}'''

import csv, json, os, re, struct
import bpy
import numpy as np
from mathutils import Matrix, Vector

PARTS = json.loads(PARTS_JSON)
SOCK = "ws_type"
BAD = re.compile(r'[<>:"/\\|?*]')


def is_helper(ob):
    """Kit-bashing utilities, not parts: ND / BoxCutter helpers, WS_ objects."""
    if ob.type != 'MESH' or ob.get(SOCK) is not None:
        return True
    if ob.name.startswith(("WS_", "_bc")):
        return True
    return any(c.name.startswith(("ND.", "WS_Connectors")) for c in ob.users_collection)


def base_name(name):
    return re.sub(r"\.\d{3}$", "", name)


def part_type(ob):
    if base_name(ob.name) in PART_TYPES:
        return PART_TYPES[base_name(ob.name)]
    for c in ob.users_collection:
        if c.name in COLLECTION_TYPES:
            return COLLECTION_TYPES[c.name]
    return ob.users_collection[0].name if ob.users_collection else "Unsorted"


def destination(ob, blend):
    hit = PARTS.get(ob.name)
    folder = hit[0] if hit else f"_Unsorted/From {blend}"
    rel = f"{folder}/{part_type(ob)}/{BAD.sub('_', base_name(ob.name))}.stl"
    return rel, hit


def sockets_of(ob):
    return [c for c in ob.children if c.get(SOCK) is not None]


def own_frame(ob):
    """The part's origin in the file: location and rotation, without scale."""
    loc, rot, _ = ob.matrix_world.decompose()
    return Matrix.LocRotScale(loc, rot, Vector((1.0, 1.0, 1.0)))


# Filled in by plan_types() at the start of run().
NEW = {}        # old fit type -> name written to the library
REBASE = {}     # old fit type -> matrix: its parts' new local = R @ old local
DROP = set()    # socket object names left out (the merged-away twin on a reference part)
MOVE = {}       # socket object name -> matrix to apply to its frame
NOTES = {}      # object name -> report note


def fit_type_of(ob):
    """The fit type a part was set up for: what it is snapped as, else its collection's."""
    if ob.get("ws_snap_type"):
        return ob["ws_snap_type"]
    for c in ob.users_collection:
        if c.name in COLLECTION_FIT:
            return COLLECTION_FIT[c.name]
    return None


def part_frame(ob):
    """The frame the STL and sidecar are written in: the part's own origin,
    re-based when its fit type is merged into another one."""
    f = own_frame(ob)
    R = REBASE.get(fit_type_of(ob))
    return f @ R.inverted_safe() if R is not None else f


def plan_types(scene):
    """Work out renames and merges. A merge of B into A is exact when some
    part carries a socket of each: B's parts move onto A's socket by the
    difference between the two sockets on that part."""
    NEW.clear(); REBASE.clear(); DROP.clear(); MOVE.clear(); NOTES.clear()
    types = {t.name: t for t in getattr(scene, "ws_types", [])}

    def fit(name):
        t = types.get(name)
        if t is None:
            return Matrix.Identity(4)
        off = Matrix((t.mat[0:4], t.mat[4:8], t.mat[8:12], t.mat[12:16])) if t.captured \
            else Matrix.Identity(4)
        return Matrix.Translation((0.0, 0.0, t.gap)) @ off

    by_new = {}
    for old, new in RENAME.items():
        by_new.setdefault(new, []).append(old)
    for name in types:
        NEW.setdefault(name, RENAME.get(name, name))
    hosts = {}
    for ob in bpy.data.objects:
        for sk in sockets_of(ob):
            hosts.setdefault(ob.name, {}).setdefault(sk[SOCK], []).append(sk)
    for new, olds in by_new.items():
        olds = [o for o in olds if o in types]
        if len(olds) < 2:
            continue
        a = olds[0]
        for b in olds[1:]:
            ref = next((h for h, socks in hosts.items() if a in socks and b in socks), None)
            if ref is None:
                if max(abs(x) for row in (fit(a) - fit(b)) for x in row) > 1e-4:
                    NEW[b] = f"{new} ({b})"
                    NOTES[b] = f"kept as '{NEW[b]}': no part has both a {a} and a {b} socket to line them up"
                continue
            SA, SB = hosts[ref][a][0].matrix_world, hosts[ref][b][0].matrix_world
            R = (SA @ fit(a)).inverted_safe() @ (SB @ fit(b))
            REBASE[b] = R
            move = fit(b) @ R.inverted_safe() @ fit(a).inverted_safe()
            for h, socks in hosts.items():
                for sk in socks.get(b, []):
                    if a in socks:
                        DROP.add(sk.name)
                    else:
                        MOVE[sk.name] = move
            loc, rot, _ = R.decompose()
            NOTES[b] = (f"{b} parts re-based onto {new}: moved {loc.length:.2f} mm, "
                        f"turned {rot.angle * 57.29578:.1f} deg (from the two sockets on {ref})")


def visible_mesh(ob):
    """Triangles as you see the part, in its own frame: modifiers applied
    (except Part Sockets' WS_ print cuts) and object scale applied, location
    and rotation not. Returns an (n, 3, 3) float32 array."""
    ws = [m for m in ob.modifiers if m.name.startswith("WS_") and m.show_viewport]
    for m in ws:
        m.show_viewport = False
    try:
        if ob.modifiers and ob.name in bpy.context.view_layer.objects:
            deps = bpy.context.evaluated_depsgraph_get()
            deps.update()
            eo = ob.evaluated_get(deps)
            me = eo.to_mesh()
        else:
            eo, me = None, ob.data
        me.calc_loop_triangles()
        n = len(me.loop_triangles)
        vi = np.empty(n * 3, np.int32)
        me.loop_triangles.foreach_get("vertices", vi)
        co = np.empty(len(me.vertices) * 3, np.float32)
        me.vertices.foreach_get("co", co)
        tri = co.reshape(-1, 3)[vi.reshape(-1, 3)]
        if eo is not None:
            eo.to_mesh_clear()
    finally:
        for m in ws:
            m.show_viewport = True
    # object -> STL frame: the object's scale, plus the re-base for merged fit types
    M4 = np.array(part_frame(ob).inverted_safe() @ ob.matrix_world, np.float64)
    S, t = M4[:3, :3], M4[:3, 3]
    if np.abs(S - np.eye(3)).max() > 1e-6 or np.abs(t).max() > 1e-6:
        tri = (tri.reshape(-1, 3) @ S.T + t).reshape(-1, 3, 3).astype(np.float32)
        if np.linalg.det(S) < 0:          # mirrored by a negative scale: keep normals outward
            tri = tri[:, ::-1, :].copy()
    return tri


def write_stl(path, ob):
    tri = visible_mesh(ob)
    n = len(tri)
    nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    ln = np.linalg.norm(nrm, axis=1, keepdims=True)
    ln[ln == 0] = 1.0
    rec = np.zeros(n, dtype=[("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")])
    rec["n"] = nrm / ln
    rec["v"] = tri.reshape(n, 9)
    head = f"PartSockets lift {ob.name}".encode("utf-8", "replace")[:80].ljust(80, b" ")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        f.write(head + struct.pack("<I", n))
        f.write(rec.tobytes())
    os.replace(tmp, path)
    return n


def flat(m):
    return [round(x, 6) for row in m for x in row]


def type_snapshot(scene, names):
    out = {}
    types = {t.name: t for t in getattr(scene, "ws_types", [])}
    order = list(RENAME)
    for n in sorted(names, key=lambda x: (order.index(x) if x in order else len(order), x)):
        if NEW.get(n, n) in out:
            continue
        t = types.get(n)
        out[NEW.get(n, n)] = ({"captured": bool(t.captured), "gap": float(t.gap),
                   "mat": [float(x) for x in t.mat] if t.captured else None}
                  if t else {"captured": False, "gap": 0.0, "mat": None})
    return out


def sidecar(ob, scene, source):
    inv = part_frame(ob).inverted_safe()
    socks = []
    for s in sockets_of(ob):
        if s.name in DROP:
            continue
        # relative to the part's origin - the STL's frame
        mw = s.matrix_world @ MOVE[s.name] if s.name in MOVE else s.matrix_world
        loc, rot, _ = (inv @ mw).decompose()
        props = {}
        for k in s.keys():
            v = s[k]
            if k.startswith("ws_") and k != SOCK and isinstance(v, (str, int, float)):
                props[k] = v
        socks.append({"type": NEW.get(s[SOCK], s[SOCK]), "was": s[SOCK], "name": s.name,
                      "matrix": flat(Matrix.LocRotScale(loc, rot, Vector((1, 1, 1)))),
                      "display_type": s.empty_display_type,
                      "display_size": float(s.empty_display_size),
                      "props": props})
    # per-part fits (Store Per-Part Fit): this part's own offset for a type,
    # e.g. a jump pack that sits lower than other backpacks
    fits = {NEW.get(k[len("ws_fit::"):], k[len("ws_fit::"):]): [float(x) for x in ob[k]]
            for k in ob.keys() if k.startswith("ws_fit::") and len(ob[k]) == 16}
    if not socks and not fits:
        return None
    old = {s["was"] for s in socks} | {k[len("ws_fit::"):] for k in ob.keys() if k.startswith("ws_fit::")}
    if ob.get("ws_snap_type"):
        old.add(ob["ws_snap_type"])
    return {"schemaVersion": 1, "part": base_name(ob.name), "source": source,
            "sockets": socks, "fits": fits, "types": type_snapshot(scene, old)}


def score(ob):
    # which copy wins when several objects are the same part
    return (len(sockets_of(ob)) > 0, bool(ob.get("ws_snap_type")),
            base_name(ob.name) == ob.name, -len(ob.name))


def save_joint_set(scene):
    """Save the captured fit types to Part Sockets' Joint Library under their
    library names, through Part Sockets' own reader/writer."""
    import sys
    mod = next((m for n, m in sys.modules.items()
                if n.endswith("part_sockets.joints") and hasattr(m, "save_library")), None)
    if mod is None:
        raise RuntimeError("Part Sockets isn't enabled")
    data = mod.load_library_for_write()
    if data is None:
        raise RuntimeError("the joint library exists but can't be read")
    specs, seen = [], set()
    order = list(RENAME)
    for t in sorted(scene.ws_types, key=lambda t: order.index(t.name) if t.name in order else len(order)):
        name = NEW.get(t.name, t.name)
        if not t.captured or name in seen:
            continue
        seen.add(name)
        specs.append({"name": name, "captured": True, "mat": [float(x) for x in t.mat],
                      "gap": float(t.gap)})
    data[JOINT_SET] = {"types": specs, "source": os.path.basename(bpy.data.filepath) or "unsaved"}
    if not mod.save_library(data):
        raise RuntimeError("could not write the joint library")
    mod.invalidate_joint_cache()
    return len(specs)


def run():
    scene = bpy.context.scene
    blend = os.path.splitext(os.path.basename(bpy.data.filepath))[0] or "unsaved"
    lib = bpy.path.abspath(LIBRARY)
    plan_types(scene)
    # one group per source file (copies of the same part), or per name for
    # parts with no known source
    groups = {}
    for ob in bpy.data.objects:
        if is_helper(ob):
            continue
        rel, hit = destination(ob, blend)
        key = ("src", hit[1]) if hit else ("rel", rel.lower())
        groups.setdefault(key, []).append((ob, rel, hit))
    # different source files that would land on the same name (Mar Fil's
    # HelmetsUpdates and HelmetsUpdates-1 both have a 1.stl): add the
    # source folder to the name so neither overwrites the other
    by_rel = {}
    for key, entries in groups.items():
        by_rel.setdefault(entries[0][1].lower(), []).append(key)
    for rel_l, keys in by_rel.items():
        if len(keys) < 2:
            continue
        for key in keys:
            fixed = []
            for ob, rel, hit in groups[key]:
                tag = hit[1].split("/")[-2] if hit else ob.name
                fixed.append((ob, rel[:-4] + f" ({BAD.sub('_', tag)}).stl", hit))
            groups[key] = fixed

    rows, written, kept, dupes, variants = [], 0, 0, 0, 0

    def signature(o):
        co = np.empty(len(o.data.vertices) * 3, np.float32)
        o.data.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        box = np.round(np.concatenate([co.min(0), co.max(0)]), 3) if len(co) else ()
        scale = tuple(np.round(o.matrix_world.to_scale(), 3))
        mods = tuple(m.name for m in o.modifiers if not m.name.startswith("WS_"))
        return (len(o.data.polygons), tuple(box), scale, mods), co

    def socket_set(o):
        inv = part_frame(o).inverted_safe()
        return {(s[SOCK], tuple(np.round((inv @ s.matrix_world).translation, 3)))
                for s in sockets_of(o)}

    planned = set()

    def unique(rel):
        stem, n = rel[:-4], 2
        while rel.lower() in planned:
            rel = f"{stem} ({n}).stl"
            n += 1
        planned.add(rel.lower())
        return rel

    def export(ob, rel, hit, note=""):
        nonlocal written, kept
        path = os.path.join(lib, *rel.split("/"))
        _, co = signature(ob)
        lo = co.min(0).tolist() if len(co) else [0, 0, 0]
        hi = co.max(0).tolist() if len(co) else [0, 0, 0]
        origin = "unknown source"
        if hit:
            moved = max(abs(a - b) for a, b in zip(lo + hi, hit[2] + hit[3]))
            origin = "set by you" if moved > 0.05 else "as exported"
        notes = [note] if note else []
        if fit_type_of(ob) in REBASE:
            notes.append(NOTES[fit_type_of(ob)])
        sc = ob.matrix_world.to_scale()
        if max(abs(v - 1) for v in sc) > 1e-4:
            notes.append("scene scale %.3g/%.3g/%.3g applied" % tuple(sc)
                         + (" (mirrored)" if sc[0] * sc[1] * sc[2] < 0 else ""))
        mods = [m.name for m in ob.modifiers if not m.name.startswith("WS_")]
        if mods:
            notes.append("modifiers applied: " + ", ".join(mods))
        side = sidecar(ob, scene, {"blend": blend, "object": ob.name,
                                   "file": hit[1] if hit else ""})
        if side and side["fits"]:
            notes.append("per-part fit: " + ", ".join(sorted(side["fits"])))
        status = "would write" if DRY_RUN else "written"
        if os.path.exists(path) and not OVERWRITE:
            status = "exists - left alone"
            kept += 1
        elif not DRY_RUN:
            write_stl(path, ob)
            if side:
                tmp = path[:-4] + ".sockets.json.tmp"
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(side, f, indent=1)
                os.replace(tmp, path[:-4] + ".sockets.json")
            written += 1
        rows.append([ob.name, part_type(ob), rel, hit[1] if hit else "", origin,
                     len(side["sockets"]) if side else 0, status, "; ".join(notes)])

    for key in sorted(groups, key=lambda k: groups[k][0][1].lower()):
        entries = sorted(groups[key], key=lambda e: score(e[0]), reverse=True)
        # Copies with the same mesh, origin, scale and modifiers are one part;
        # a copy that differs in any of those, or carries sockets the kept
        # one doesn't, is your variant and is kept under its own name.
        clusters = {}
        for e in entries:
            clusters.setdefault(signature(e[0])[0], []).append(e)
        lead = None
        for members in clusters.values():
            keep = members[0]
            extra = [m for m in members[1:] if not socket_set(m[0]) <= socket_set(keep[0])]
            for i, (ob, rel, hit) in enumerate([keep] + extra):
                if lead is None:
                    export(ob, unique(rel), hit)
                    lead = ob.name
                else:
                    variants += 1
                    folder = rel.rsplit("/", 1)[0]
                    export(ob, unique(f"{folder}/{BAD.sub('_', ob.name)}.stl"), hit,
                           f"variant of {lead} (different mesh, origin, scale or sockets)")
            for other, rel, hit in members[1:]:
                if (other, rel, hit) in extra:
                    continue
                dupes += 1
                rows.append([other.name, part_type(other), rel, hit[1] if hit else "", "",
                             len(sockets_of(other)), "skipped - identical copy of " + keep[0].name, ""])

    for ob in bpy.data.objects:
        if ob.type in {'CURVE', 'SURFACE', 'META', 'FONT'} and \
                any(c.name in COLLECTION_TYPES for c in ob.users_collection):
            rows.append([ob.name, part_type(ob), "", "", "", 0,
                         "not exported - " + ob.type.lower(),
                         "convert to mesh if it belongs in the library"])

    for old in sorted(NEW):
        if NEW[old] != old:
            rows.append(["(fit type) " + old, "", "", "", "", "", "renamed to " + NEW[old],
                         NOTES.get(old, "")])

    os.makedirs(lib, exist_ok=True)
    report = os.path.join(lib, f"_lift_report_{blend}.csv")
    with open(report, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["object", "type", "library path", "Mar Fil source", "origin",
                    "sockets", "status", "notes"])
        w.writerows(rows)

    saved = ""
    if JOINT_SET and not DRY_RUN and len(getattr(scene, "ws_types", [])):
        try:
            n = save_joint_set(scene)
            saved = f", {n} fit types saved to Joint Library as '{JOINT_SET}'"
        except Exception as exc:
            saved = f", fit types NOT saved ({exc})"
    msg = (f"{'DRY RUN - ' if DRY_RUN else ''}{len(groups) + variants} parts "
           f"({variants} of them your variants): {written} written, {kept} already there, "
           f"{dupes} identical copies skipped{saved}. Report: {report}")
    print(msg)
    return msg


if __name__ == "__main__":
    result = run()
    try:
        bpy.context.window_manager.popup_menu(
            lambda self, ctx: self.layout.label(text=result), title="Lift parts", icon='INFO')
    except Exception:
        pass
