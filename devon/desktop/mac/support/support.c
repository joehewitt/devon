#include <python/Python.h>
#include <python/pymactoolbox.h>
#include <Carbon/Carbon.h>

typedef struct EventHotKeyRefObject {
  PyObject_HEAD
  EventHotKeyRef ob_itself;
} EventHotKeyRefObject;

static PyObject
*HotKeyAddress(PyObject *self, PyObject *args) {
  PyObject *v;
  if (!PyArg_ParseTuple(args, "O", &v))
    return NULL;
  return PyInt_FromLong((int)((EventHotKeyRefObject *)v)->ob_itself);
}

static PyMethodDef _devonModuleMethods[] = {
  {"HotKeyAddress", HotKeyAddress, METH_VARARGS,
   "HotKeyAddress(_CarbonEvt.EventHotKeyRef) -> integer\n\n"
   "Return the address of the underlying EventHotKeyRef (passed as data1 in hot key NSEvents)."},
  {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC
init_devon_macsupport(void) {
  (void)Py_InitModule("_devon_macsupport", _devonModuleMethods);
}
