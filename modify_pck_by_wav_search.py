import os
import shutil
import hashlib
import json
from functools import partial

kouqiu_path = '口球.jpeg'
kouqiu = open(kouqiu_path, "rb")

def md5sum(filename):
    with open(filename, mode='rb') as f:
        d = hashlib.md5()
        for buf in iter(partial(f.read, 128), b''):
            d.update(buf)
    return d.hexdigest()

def bytesmd5sum(f):
    d = hashlib.md5()
    d.update(f)
    return d.hexdigest()

# 将字符串强制类型转化为数字
def hex_string_to_hex(hex_string):
    hex_num = 0
    i = 0
    for every_char in hex_string:
        hex_num = hex_num + every_char * 256 ** i
        i = i + 1
    return hex_num
 
 
# 将数字强制类型转化为bytes
def hex_to_hex_bytes(hex_num):
    # 先将其转化为bytes
    hex_bytes = []
    while hex_num > 256:
        single_hex_bytes = hex_num % 256
        hex_bytes = hex_bytes + [single_hex_bytes]
        hex_num = hex_num // 256
 
    single_hex_bytes = hex_num % 256
    hex_bytes = hex_bytes + [single_hex_bytes]
 
    return bytearray(hex_bytes)

def generate_new_pck(pck_name, pck_path, target_wav_serial_num):
    wav = kouqiu
    wav_path = kouqiu_path
    new_pck_path = os.path.join("newpck", pck_name)
    if os.path.exists(new_pck_path):
        shutil.copyfile(new_pck_path, new_pck_path+".new")
        pck_path = new_pck_path+".new"
    with open(pck_path, "rb") as pck:
        with open(new_pck_path, "wb+") as new_pck:
                
            # 获取pck文件中包含的wav文件数量
            pck.seek(0x00000038, 0)
            pck_wav_num = hex_string_to_hex(pck.read(2))

            # 计算pck文件头部大小
            pck_head_size = initial_offset + pck_wav_num * 24
            # 将pck文件头部信息全部复制进new_pck中
            pck.seek(0, 0)
            new_pck.write(pck.read(pck_head_size))

            # 获取替换文件的大小
            new_wav_size = os.path.getsize(wav_path)
            # 获取被替换文件的大小
            pck.seek(initial_offset + target_wav_serial_num * 24 - 24 + 13, 0)
            pck_wav_size = hex_string_to_hex(pck.read(4))

            # 计算文件大小差值
            size_variation = new_wav_size - pck_wav_size

            # 对接下来new_pck头部信息进行调整
            for i_wav_site in range(target_wav_serial_num + 1, pck_wav_num + 1, 1):
                # 调整文件起始点信息
                new_pck.seek(initial_offset + i_wav_site * 24 - 24 + 17, 0)

                i_new_pck_wav_site = hex_string_to_hex(new_pck.read(4))
                i_new_pck_wav_site = i_new_pck_wav_site + size_variation

                new_pck.seek(initial_offset + i_wav_site * 24 - 24 + 17, 0)
                new_pck.write(hex_to_hex_bytes(i_new_pck_wav_site))

            # 调整文件大小信息
            new_pck.seek(initial_offset + target_wav_serial_num * 24 - 24 + 13, 0)
            new_pck.write(hex_to_hex_bytes(new_wav_size))

            # 复制实体wav数据到new_pck中
            # 计算target_wav之前的数据大小
            pck.seek(initial_offset + target_wav_serial_num * 24 - 24 + 17, 0)
            target_wav_site = hex_string_to_hex(pck.read(4))

            # 复制target_wav之前的数据
            pck.seek(pck_head_size, 0)
            new_pck.seek(0, 2)
            new_pck.write(pck.read(target_wav_site - pck_head_size))

            # 复制new_wav到target_wav_site
            wav.seek(0, 0)
            new_pck.seek(0, 2)
            new_pck.write(wav.read(-1))

            # 复制target_wav之后的信息
            pck.seek(0, 0)
            new_pck.seek(0, 2)
            new_pck.write(pck.read(-1)[target_wav_site + pck_wav_size:])
    
    if os.path.exists(new_pck_path+".new"):
        os.remove(new_pck_path+".new")

if __name__ == '__main__':

    initial_offset = 0x0000003B #默认PC端
 
    genshin_path = input("请输入原神根目录路径（X:\\xxx\\Genshin Impact）：")
    if genshin_path == "":
        print("未输入路径，默认使用C:\\Genshin Impact")
        genshin_path = "C:\\Genshin Impact"
    pck_dir_path = os.path.join(genshin_path, "Genshin Impact Game\\YuanShen_Data\\StreamingAssets\\Audio\\GeneratedSoundBanks\\Windows\\Chinese\\")
    if not os.path.exists(genshin_path) or not os.path.exists(pck_dir_path):
        print(f"{genshin_path}路径不存在或路径不是原神根目录")
        os.system("pause")
        exit()
    persistant_path = os.path.join(genshin_path, "Genshin Impact Game\\YuanShen_Data\\Persistent\\AudioAssets\\Chinese")

    # 获取所有文件
    pck_list = os.listdir(pck_dir_path)
    
    wav_dict = dict()

    for _, _, files in os.walk("wav"):
        for filename in files:
            wav_path = os.path.join("wav", filename)
            with open(wav_path, "rb") as f:
                wav_file = f.read()
                wav_dict[md5sum(wav_path)] = (wav_file, filename)

    for pck_name in pck_list:
        if pck_name.split('.')[-1] != 'pck' or not pck_name.startswith('External'):
            continue
        pck_path = os.path.join(pck_dir_path, pck_name)
        print("\n\nProcessing:", pck_name)
        with open(pck_path, "rb") as pck:
            # 获取pck文件中包含的wav文件数量
            pck.seek(0x00000038, 0)
            pck_wav_num = hex_string_to_hex(pck.read(2))

            for pck_wav_index in range(1, pck_wav_num + 1):

                #读当前wav的size
                pck.seek(initial_offset + pck_wav_index * 24 - 24 + 13, 0)
                pck_wav_size = hex_string_to_hex(pck.read(4))

                #seek至当前wav的位置
                pck.seek(initial_offset + pck_wav_index * 24 - 24 + 17, 0)
                target_wav_site = hex_string_to_hex(pck.read(4))
                pck.seek(target_wav_site)

                # 比较 wav 文件内容
                pck_wav = pck.read(pck_wav_size)
                pck_wav_md5 = bytesmd5sum(pck_wav)
                if pck_wav_md5 in wav_dict:
                    wav_file, wav_name = wav_dict[pck_wav_md5]
                    print(f'found wav {wav_name} in pck {pck_name} no.{pck_wav_index}')
                    generate_new_pck(pck_name, pck_path, pck_wav_index)
    
    newpck_list = os.listdir("newpck")
    for pck_name in newpck_list:
        backup_pck_path = os.path.join("backuppck", pck_name)
        pck_path = os.path.join(pck_dir_path, pck_name)
        new_pck_path = os.path.join("newpck", pck_name)
        persistant_pck_path = os.path.join(persistant_path, pck_name)
        if not os.path.exists(backup_pck_path):
            shutil.copyfile(pck_path, backup_pck_path)
        print("Copying ", new_pck_path, " to ", pck_path)
        shutil.copyfile(new_pck_path, pck_path)
        if os.path.exists(persistant_pck_path):
            print("Copying ", new_pck_path, " to ", persistant_pck_path)
            shutil.copyfile(new_pck_path, persistant_pck_path)

    
    audio_versions_streaming_path = os.path.join(genshin_path, "Genshin Impact Game\\YuanShen_Data\\StreamingAssets\\Audio\\audio_versions_streaming")
    new_audio_versions_streaming_path = "audio_versions_streaming"
    with open(audio_versions_streaming_path, 'r') as f:
        with open(new_audio_versions_streaming_path, 'w') as wf:
            for line in f:
                line_json = json.loads(line)
                name = line_json.get('remoteName').split('/')
                if name[0] != 'Chinese' or name[1] not in newpck_list:
                    wf.write(line)
                    continue
                wline = dict()
                wline['remoteName'] = line_json.get('remoteName')
                pck_path = os.path.join(pck_dir_path, name[1])
                wline['md5'] = md5sum(pck_path)
                wline['fileSize'] = os.path.getsize(pck_path)
                print(json.dumps(wline))
                wf.write(json.dumps(wline)+'\n')
    print("Copying ", new_audio_versions_streaming_path, " to ", audio_versions_streaming_path)
    shutil.copyfile(new_audio_versions_streaming_path, audio_versions_streaming_path)

    print("一键口球成功！")
    print("取消口球方法：原神客户端中检测游戏文件完整性")
    os.system("pause")
