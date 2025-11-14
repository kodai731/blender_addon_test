layout(triangles) in;
layout(line_strip, max_vertices = 6) out;

in vec3 vNormal[];
in vec4 vPosition[];

uniform float normalLength;

void main()
{
    for (int i = 0; i < 3; i++)
    {
        // 頂点位置
        gl_Position = vPosition[i];
        EmitVertex();

        // 法線の先端位置
        gl_Position = vPosition[i] + vec4(vNormal[i] * normalLength, 0.0);
        EmitVertex();

        EndPrimitive();
    }
}
