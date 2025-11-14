layout(triangles) in;
layout(line_strip, max_vertices = 18) out;

in vec3 vNormal[];
in vec4 vPosition[];

uniform float normalLength;
uniform float arrowSize;

// 法線に垂直なベクトルを計算
vec3 getPerpendicularVector(vec3 n)
{
    // ワールドアップベクトルと法線が平行でない場合はそれを使用
    vec3 up = vec3(0.0, 0.0, 1.0);
    if (abs(dot(n, up)) > 0.99)
    {
        up = vec3(1.0, 0.0, 0.0);
    }
    return normalize(cross(n, up));
}

void main()
{
    for (int i = 0; i < 3; i++)
    {
        vec3 normal = normalize(vNormal[i]);
        vec4 startPos = vPosition[i];
        vec4 endPos = vPosition[i] + vec4(normal * normalLength, 0.0);

        // 法線の線を描画
        gl_Position = startPos;
        EmitVertex();
        gl_Position = endPos;
        EmitVertex();
        EndPrimitive();

        // 矢印の羽を描画
        vec3 perpendicular1 = getPerpendicularVector(normal);
        vec3 perpendicular2 = normalize(cross(normal, perpendicular1));

        float arrowLength = normalLength * arrowSize;

        // 羽の方向：法線の逆方向 + 垂直方向
        vec3 arrowDir1 = normalize(-normal + perpendicular1);
        vec3 arrowDir2 = normalize(-normal + perpendicular2);
        vec3 arrowDir3 = normalize(-normal - perpendicular1);
        vec3 arrowDir4 = normalize(-normal - perpendicular2);

        // 羽1
        gl_Position = endPos;
        EmitVertex();
        gl_Position = endPos + vec4(arrowDir1 * arrowLength, 0.0);
        EmitVertex();
        EndPrimitive();

        // 羽2
        gl_Position = endPos;
        EmitVertex();
        gl_Position = endPos + vec4(arrowDir2 * arrowLength, 0.0);
        EmitVertex();
        EndPrimitive();

        // 羽3
        gl_Position = endPos;
        EmitVertex();
        gl_Position = endPos + vec4(arrowDir3 * arrowLength, 0.0);
        EmitVertex();
        EndPrimitive();

        // 羽4
        gl_Position = endPos;
        EmitVertex();
        gl_Position = endPos + vec4(arrowDir4 * arrowLength, 0.0);
        EmitVertex();
        EndPrimitive();
    }
}
