in vec3 position;
uniform mat4 ModelViewProjectionMatrix;
void main()
{
    gl_Position = ModelViewProjectionMatrix * vec4(position, 1.0);
}
