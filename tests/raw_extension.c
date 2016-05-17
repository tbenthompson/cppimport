#include <Python.h>

#if PY_MAJOR_VERSION >= 3
    #define MOD_INIT(name) PyMODINIT_FUNC PyInit_##name(void)
    #define MOD_DEF(ob, name, doc, methods) \
        static struct PyModuleDef moduledef = { \
            PyModuleDef_HEAD_INIT, name, doc, -1, methods, }; \
        ob = PyModule_Create(&moduledef);
    #define MOD_SUCCESS_VAL(val) val
#else
    #define MOD_INIT(name) PyMODINIT_FUNC init##name(void)
    #define MOD_DEF(ob, name, doc, methods) \
        ob = Py_InitModule3(name, methods, doc);
    #define MOD_SUCCESS_VAL(val)
#endif

static PyObject* add(PyObject* self, PyObject* args) {
    int a, b;
    int class = 1;
    if (!PyArg_ParseTuple(args, "ii", &a, &b)) {
        return NULL;
    }
    return Py_BuildValue("i", a + b);
}

static PyMethodDef methods[] = {
    {"add", add, METH_VARARGS, ""},
    {NULL}
};

MOD_INIT(raw_extension) {
    PyObject* m;
    MOD_DEF(m, "raw_extension", "", methods)
    return MOD_SUCCESS_VAL(m);
}
