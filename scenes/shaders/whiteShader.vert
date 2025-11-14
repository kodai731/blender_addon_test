in vec3 position;
in vec3 normal;
uniform mat4 ModelViewProjectionMatrix;
uniform mat4 NormalMatrix;

out vec3 vNormal;
out vec4 vPosition;

void main()
{
    vPosition = ModelViewProjectionMatrix * vec4(position, 1.0);
    vNormal = normalize(mat3(NormalMatrix) * normal);
    gl_Position = vPosition;
}
