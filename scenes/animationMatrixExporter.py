import bpy
from pathlib import Path
import json
from datetime import datetime

def get_script_directory():
    """スクリプトのディレクトリを取得（Blenderテキストエディタ対応）"""
    # .blendファイルが保存されている場合、そのディレクトリを使用
    if bpy.data.filepath:
        return Path(bpy.data.filepath).parent
    else:
        # 保存されていない場合はエラー
        raise RuntimeError("❌ .blendファイルを保存してから実行してください")

# 古いハンドラをクリーンアップ
if hasattr(bpy.types.Scene, "_animation_matrix_export_handlers"):
    print(f"🧹 既存のハンドラをクリーンアップ中... ({len(bpy.types.Scene._animation_matrix_export_handlers)}個)")
    for handler in bpy.types.Scene._animation_matrix_export_handlers:
        try:
            if handler in bpy.app.handlers.frame_change_post:
                bpy.app.handlers.frame_change_post.remove(handler)
                print(f"   ✅ ハンドラを削除しました")
        except Exception as e:
            print(f"   ⚠️ ハンドラ削除エラー: {e}")
    bpy.types.Scene._animation_matrix_export_handlers.clear()

# ハンドラリストを初期化
bpy.types.Scene._animation_matrix_export_handlers = []

# 出力設定
output_mode = "file"  # "console" または "file"
output_file_path = None

if output_mode == "file":
    try:
        script_dir = get_script_directory()
        output_file_path = script_dir / f"animation_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        print(f"📁 出力ファイル: {output_file_path}")
    except Exception as e:
        print(f"⚠️ ファイルパス取得エラー、コンソール出力に切り替えます: {e}")
        output_mode = "console"

# 全フレームのデータを保存するリスト（ファイル出力用）
all_frames_data = []

# 前フレームのデータを保存（変化量計算用）
previous_frame_data = {}

def matrix_to_list(matrix):
    """Matrixオブジェクトをリストに変換"""
    return [list(row) for row in matrix]

def vector_to_list(vector):
    """Vectorをリストに変換"""
    return [round(v, 6) for v in vector]

def quaternion_to_list(quat):
    """Quaternionをリストに変換 (w, x, y, z)"""
    return [round(quat.w, 6), round(quat.x, 6), round(quat.y, 6), round(quat.z, 6)]

def get_keyframe_info(obj):
    """オブジェクトのキーフレーム情報を取得"""
    keyframe_info = {
        "has_keyframes": False,
        "channels": []
    }

    if obj.animation_data and obj.animation_data.action:
        action = obj.animation_data.action
        frame = bpy.context.scene.frame_current

        for fcurve in action.fcurves:
            # 現在のフレームにキーフレームがあるか確認
            for keyframe in fcurve.keyframe_points:
                if abs(keyframe.co[0] - frame) < 0.01:  # フレーム番号の誤差許容
                    keyframe_info["has_keyframes"] = True
                    keyframe_info["channels"].append({
                        "data_path": fcurve.data_path,
                        "array_index": fcurve.array_index,
                        "value": round(keyframe.co[1], 6),
                        "interpolation": keyframe.interpolation
                    })

    return keyframe_info

def export_frame_data(scene):
    """現在のフレームのデータをエクスポート"""
    global previous_frame_data

    frame = scene.frame_current
    fps = scene.render.fps / scene.render.fps_base
    time = frame / fps

    # フレーム情報
    frame_data = {
        "frame": frame,
        "time": round(time, 4),
        "fps": round(fps, 2),
        "meshes": []
    }

    # 全メッシュオブジェクトを取得
    mesh_objects = [obj for obj in scene.objects if obj.type == 'MESH']

    for obj in mesh_objects:
        # ワールド行列から位置・回転・スケールを分解
        world_matrix = obj.matrix_world
        loc, rot_quat, scale = world_matrix.decompose()

        mesh_info = {
            "name": obj.name,
            # 行列情報
            "world_matrix": matrix_to_list(world_matrix),
            "local_matrix": matrix_to_list(obj.matrix_local),
            # 分解された値
            "location": vector_to_list(loc),
            "rotation_euler": vector_to_list(obj.rotation_euler),
            "rotation_quaternion": quaternion_to_list(rot_quat),
            "scale": vector_to_list(scale),
            # キーフレーム情報
            "keyframe_info": get_keyframe_info(obj)
        }

        # 前フレームとの差分を計算
        if obj.name in previous_frame_data:
            prev = previous_frame_data[obj.name]

            # Eulerオブジェクトは各要素を個別に減算
            from mathutils import Vector
            euler_diff = Vector([
                obj.rotation_euler[0] - prev["rotation_euler"][0],
                obj.rotation_euler[1] - prev["rotation_euler"][1],
                obj.rotation_euler[2] - prev["rotation_euler"][2]
            ])

            delta = {
                "location": vector_to_list(loc - prev["location"]),
                "rotation_euler": vector_to_list(euler_diff),
                "scale": vector_to_list(scale - prev["scale"]),
                "distance_moved": round((loc - prev["location"]).length, 6)
            }
            mesh_info["delta"] = delta
            mesh_info["changed"] = delta["distance_moved"] > 0.0001
        else:
            mesh_info["changed"] = True  # 初回フレーム

        # 次回の差分計算用に保存
        from mathutils import Euler
        previous_frame_data[obj.name] = {
            "location": loc.copy(),
            "rotation_euler": [obj.rotation_euler[0], obj.rotation_euler[1], obj.rotation_euler[2]],
            "scale": scale.copy()
        }

        frame_data["meshes"].append(mesh_info)

    # 出力処理
    if output_mode == "console":
        print("=" * 80)
        print(f"📊 Frame: {frame} | Time: {time:.4f}s | FPS: {fps:.2f}")
        print("-" * 80)

        for mesh_info in frame_data["meshes"]:
            # 変化がないオブジェクトはスキップ（オプション：コメントアウトで全て表示）
            # if not mesh_info["changed"]:
            #     continue

            change_mark = "🔴" if mesh_info["changed"] else "⚪"
            key_mark = "🔑" if mesh_info["keyframe_info"]["has_keyframes"] else ""
            print(f"\n{change_mark} {key_mark} Mesh: {mesh_info['name']}")

            print(f"   📍 Location: {mesh_info['location']}")
            print(f"   🔄 Rotation (Euler): {mesh_info['rotation_euler']}")
            print(f"   🔄 Rotation (Quat):  {mesh_info['rotation_quaternion']}")
            print(f"   📏 Scale: {mesh_info['scale']}")

            # 変化量を表示
            if "delta" in mesh_info:
                print(f"   📊 Delta Location: {mesh_info['delta']['location']}")
                print(f"   📊 Distance Moved: {mesh_info['delta']['distance_moved']}")

            # キーフレーム情報を表示
            if mesh_info["keyframe_info"]["has_keyframes"]:
                print(f"   🔑 Keyframe Channels:")
                for ch in mesh_info["keyframe_info"]["channels"]:
                    print(f"      - {ch['data_path']}[{ch['array_index']}] = {ch['value']} ({ch['interpolation']})")

            print(f"\n   🌍 World Matrix:")
            for i, row in enumerate(mesh_info['world_matrix']):
                print(f"      [{i}] {[round(v, 6) for v in row]}")

        print("=" * 80)

    elif output_mode == "file":
        all_frames_data.append(frame_data)

# アニメーション停止時にファイルに保存する関数
def save_to_file():
    """収集したデータをファイルに保存"""
    if output_mode == "file" and output_file_path and all_frames_data:
        try:
            with open(output_file_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "export_info": {
                        "date": datetime.now().isoformat(),
                        "blend_file": bpy.data.filepath,
                        "total_frames": len(all_frames_data)
                    },
                    "frames": all_frames_data
                }, f, indent=2, ensure_ascii=False)
            print(f"💾 データを保存しました: {output_file_path}")
            print(f"   総フレーム数: {len(all_frames_data)}")
        except Exception as e:
            print(f"❌ ファイル保存エラー: {e}")
    elif output_mode == "console":
        print("⚠️ コンソール出力モードのため、ファイル保存はスキップされます")
    elif not all_frames_data:
        print("⚠️ 保存するデータがありません。アニメーションを再生してください")

def on_frame_change(scene):
    """フレーム変更時のコールバック"""
    try:
        export_frame_data(scene)
    except Exception as e:
        print(f"❌ フレームデータエクスポートエラー: {e}")
        import traceback
        traceback.print_exc()

# 最後のフレーム番号を記録（再生完了検出用）
last_frame_number = None

def check_animation_end(scene):
    """アニメーション再生終了時に自動保存"""
    global last_frame_number

    current_frame = scene.frame_current
    end_frame = scene.frame_end

    # 最終フレームに到達し、かつファイル出力モードの場合
    if output_mode == "file" and current_frame == end_frame and last_frame_number != end_frame:
        last_frame_number = end_frame
        # 少し遅延させてから保存（データの確実な記録のため）
        import threading
        def delayed_save():
            import time
            time.sleep(0.5)
            save_to_file()
        threading.Thread(target=delayed_save, daemon=True).start()

# ハンドラを登録
bpy.app.handlers.frame_change_post.append(on_frame_change)
bpy.app.handlers.frame_change_post.append(check_animation_end)
bpy.types.Scene._animation_matrix_export_handlers.append(on_frame_change)
bpy.types.Scene._animation_matrix_export_handlers.append(check_animation_end)

print("✅ アニメーション行列エクスポーターを初期化しました")
print(f"   出力モード: {output_mode}")
print(f"   対象メッシュ数: {len([obj for obj in bpy.context.scene.objects if obj.type == 'MESH'])}")
if output_mode == "file" and output_file_path:
    print(f"   出力先: {output_file_path}")
print("\n▶️ アニメーションを再生すると、フレーム毎にデータが出力されます")

# 現在のフレームのデータを即座に出力（初期確認用）
print("\n🔍 現在のフレームのデータ:")
export_frame_data(bpy.context.scene)

# ファイルモードの場合の使い方を表示
if output_mode == "file":
    print("\n" + "=" * 80)
    print("📋 使い方:")
    print("   1. タイムラインでアニメーションを最初から最後まで再生")
    print("   2. 最終フレームに到達すると自動保存されます")
    print("   3. または、Pythonコンソールで手動保存: save_to_file()")
    print("=" * 80)
