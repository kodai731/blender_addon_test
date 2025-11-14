import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from pathlib import Path

def get_script_directory():
    """スクリプトのディレクトリを取得（Blenderテキストエディタ対応）"""
    # .blendファイルが保存されている場合、そのディレクトリを使用
    if bpy.data.filepath:
        return Path(bpy.data.filepath).parent
    else:
        # 保存されていない場合はエラー
        raise RuntimeError("❌ .blendファイルを保存してから実行してください")

def load_shader(shader_name):
    """シェーダーファイルを読み込む"""
    script_dir = get_script_directory()
    shader_path = script_dir / "shaders" / shader_name

    try:
        with open(shader_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"❌ シェーダーファイルが見つかりません: {shader_path}")
        print(f"📁 検索場所: {script_dir / 'shaders'}")
        raise

# 古いハンドラとデータを完全にクリーンアップ
if hasattr(bpy.types.SpaceView3D, "_custom_shader_handlers"):
    print(f"🧹 Cleaning up {len(bpy.types.SpaceView3D._custom_shader_handlers)} old handlers...")
    for handle in bpy.types.SpaceView3D._custom_shader_handlers:
        try:
            bpy.types.SpaceView3D.draw_handler_remove(handle, 'WINDOW')
            print(f"   Removed handler: {handle}")
        except Exception as e:
            print(f"   Failed to remove handler: {e}")
    bpy.types.SpaceView3D._custom_shader_handlers.clear()

# 古いバッチとシェーダーを削除
if hasattr(bpy.types.SpaceView3D, "_custom_shader_batch"):
    print("🧹 Cleaning up old batch...")
    bpy.types.SpaceView3D._custom_shader_batch = None
if hasattr(bpy.types.SpaceView3D, "_custom_shader"):
    print("🧹 Cleaning up old shader...")
    bpy.types.SpaceView3D._custom_shader = None

# リストを初期化
bpy.types.SpaceView3D._custom_shader_handlers = []


# シェーダーファイルを読み込む
print("📖 Loading shader files...")
vertex_shader = load_shader("whiteShader.vert")
fragment_shader = load_shader("whiteShader.frag")
print("✅ Shader files loaded successfully")

shader = gpu.types.GPUShader(vertex_shader, fragment_shader)
print("✅ Shader created successfully")

obj = bpy.context.active_object
if obj is None:
    print("❌ No active object selected!")
else:
    print(f"✅ Active object: {obj.name}, type: {obj.type}")

if obj.type != 'MESH':
    mesh = obj.to_mesh()
    print(f"✅ Converted {obj.type} to mesh")
else:
    mesh = obj.data
    print(f"✅ Using mesh data directly")

mesh.calc_loop_triangles()

# オブジェクトのワールド変換行列を取得
model_matrix = obj.matrix_world
print(f"✅ Model matrix:\n{model_matrix}")

# 頂点をワールド座標に変換
verts = [model_matrix @ v.co for v in mesh.vertices]
indices = [tuple(tri.vertices) for tri in mesh.loop_triangles]

print(f"✅ Mesh data: {len(verts)} vertices, {len(indices)} triangles")
print(f"   First 3 vertices (local): {[v.co for v in mesh.vertices[:3]]}")
print(f"   First 3 vertices (world): {verts[:3]}")
print(f"   First 3 indices: {indices[:3]}")

batch = batch_for_shader(shader, 'TRIS', {"position": verts}, indices=indices)
print(f"✅ Batch created with world coordinates")

# バッチとシェーダーを保存（再利用のため）
bpy.types.SpaceView3D._custom_shader = shader
bpy.types.SpaceView3D._custom_shader_batch = batch

def draw():
    try:
        # 保存されたシェーダーとバッチを使用
        current_shader = bpy.types.SpaceView3D._custom_shader
        current_batch = bpy.types.SpaceView3D._custom_shader_batch

        if current_shader is None or current_batch is None:
            return

        current_shader.bind()

        # MVP行列を取得して設定
        mvp = gpu.matrix.get_projection_matrix() @ gpu.matrix.get_model_view_matrix()
        current_shader.uniform_float("ModelViewProjectionMatrix", mvp)

        # 描画状態の設定
        gpu.state.depth_test_set('LESS_EQUAL')
        gpu.state.blend_set('ALPHA')

        current_batch.draw(current_shader)

        # 状態をリセット
        gpu.state.blend_set('NONE')
    except Exception as e:
        print(f"❌ Draw error: {e}")

print("🔍 Registering draw handler...")

# 描画ハンドラーを登録
handle = bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_VIEW')
bpy.types.SpaceView3D._custom_shader_handlers.append(handle)

print(f"✅ Shader overlay drawing initialized. Handler ID: {handle}")

# ビューポートの再描画をリクエスト
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        area.tag_redraw()

print("✅ Setup complete! The selected object should now be drawn in white.")

