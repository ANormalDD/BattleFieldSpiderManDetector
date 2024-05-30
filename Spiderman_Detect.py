import requests
import json
import threading
import time
import socket
from opencc import OpenCC

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
cuboids_group = {}

def is_point_in_cuboids(cuboids, x, y, z):
    for cuboid in cuboids:
        c1 = cuboid["point1"]
        c2 = cuboid["point2"]
        x_min = min(c1["x"], c2["x"])
        x_max = max(c1["x"], c2["x"])
        y_min = min(c1["y"], c2["y"]) - 0.5
        y_max = max(c1["y"], c2["y"]) + 1
        z_min = min(c1["z"], c2["z"])
        z_max = max(c1["z"], c2["z"])

        if x_min <= x <= x_max and y_min <= y <= y_max and z_min <= z <= z_max:
            return True
    return False

def dump_cuboids():
    with open('cuboids.json', 'w') as f:
        json.dump({"cuboids": cuboids_group}, f)

def load_cuboids():
    try:
        with open('cuboids.json', 'r') as f:
            global cuboids_group
            cuboids_group = json.load(f)["cuboids"]
    except FileNotFoundError:
        print("cuboids.json not found.")

def add_cuboid_json(x1, y1, z1, x2, y2, z2, group):
    if group not in cuboids_group:
        cuboids_group[group] = []
    cuboid = {"point1": {"x": x1, "y": y1, "z": z1}, "point2": {"x": x2, "y": y2, "z": z2}}
    cuboids_group[group].append(cuboid)
    dump_cuboids()

def get_players_info():
    response = requests.get("http://127.0.0.1:10086/Player/GetAllPlayerList")
    return response.json()

def get_map_name():
    try:
        response = requests.get("http://127.0.0.1:10086/Server/GetServerData")
        if response.status_code == 500:
            return "ERROR"
        response.raise_for_status()
        return response.json()["data"]["mapName"]
    except requests.exceptions.RequestException:
        return "ERROR"

def start_detect():
    while True:
        map_name = get_map_name()
        if map_name == "ID_M_LEVEL_MENU":
            print("Please be in the game.")
            continue
        if map_name == "ERROR":
            print("Server is not running.")
            continue
        if map_name not in cuboids_group:
            continue
        player_info = get_players_info()
        try :
            for player in player_info["data"]:
                x = player["x"]
                y = player["y"]
                z = player["z"]
                name = player["name"]
                if is_point_in_cuboids(cuboids_group[map_name], x, y, z):
                    send_game_chat(f'检测到蜘蛛人 {name} 请立刻下来，否则踢出（由于观战延迟可能会重复发送）')
        except Exception as e:
            print(f"An error occurred: {e}")
        time.sleep(15)


def send_game_chat(message):
    print(f"detect:{message}")
    cc = OpenCC('s2t')
    traditional_message = cc.convert(message)
    print(traditional_message)
    send_data = f"#Chat.Send#{traditional_message}".encode('utf-8')
    server_address = ("127.0.0.1", 51001)
    sock.sendto(send_data, server_address)


def start_add_point():
    while True:
        input("Press Enter to add a point...")
        group = get_map_name()
        if group == "ID_M_LEVEL_MENU":
            print("Please be in the game.")
            continue
        if group == "ERROR":
            print("Server is not running.")
            continue
        print(f"Current map: {group}")
        player_info = get_players_info()
        player_list = player_info["data"]
        x1 = player_list[0]["x"]
        y1 = player_list[0]["y"]
        z1 = player_list[0]["z"]
        print(f"Point1: x:{x1} y:{y1} z:{z1}")
        input("Press Enter to add another point...")
        player_info2 = get_players_info()
        player_list2 = player_info2["data"]
        x2 = player_list2[0]["x"]
        y2 = player_list2[0]["y"]
        z2 = player_list2[0]["z"]
        print(f"Point2: x:{x2} y:{y2} z:{z2}")
        add_cuboid_json(x1, y1, z1, x2, y2, z2, group)
        print("Added successfully.")

def main():
    load_cuboids()
    print("输入1检测蜘蛛人, 输入2添加蜘蛛人区间")
    choice = input()
    if choice == "1":
        start_detect()
    elif choice == "2":
        print("现在是添加蜘蛛人区间模式，请在你选取你要选择的区间的体对角线的两个点，先站到其中一个点上然后在本控制台按下回车，接着到另外一个点上，按下回车，即添加完成")
        start_add_point()

if __name__ == "__main__":
    main()