---
name: ctypes-ffi-bridge
description: >-
  Best practices for Python-C interoperability via ctypes, 64-bit struct memory alignment,
  explicit memory lifecycle management (malloc/free), and preventing segmentation faults.
  Use when building or debugging C shared library wrappers in Python/FastAPI.
---

# ctypes FFI Bridge: Python ↔ C Integration Safety

Normative guidelines for memory safety, deterministic lifecycle management, and ABI compatibility when integrating C shared libraries (`.so` / `.dll`) into FastAPI.

## 1. Golden Rules of ctypes Safety

1. **Explicit Return Types (`restype`)**: Never invoke a C function without explicitly declaring its `restype`. Defaulting to 32-bit `c_int` leads to pointer truncation and undefined behavior on 64-bit architectures.
2. **Explicit Argument Types (`argtypes`)**: Always declare `argtypes` for every bound C function to enforce strict runtime type checking before crossing the FFI boundary.
3. **Memory Ownership Boundary**:
   - Whoever allocates memory must be the one to free it.
   - If C allocates via `malloc`, C must export a dedicated deallocation function (e.g. `liberar_resultado(...)`). Never attempt to free C pointers using Python's GC or foreign runtime allocators.

## 2. Struct Definition & Memory Alignment

Always match C struct definitions field-for-field with exact `_fields_` ordering:

```python
import ctypes

class SalaC(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_int),
        ("capacidade", ctypes.c_int),
        ("tipo", ctypes.c_int), # 0=comum, 1=lab, 2=auditorio
        ("campus_id", ctypes.c_int),
    ]

class AlocacaoResultadoC(ctypes.Structure):
    _fields_ = [
        ("turma_id", ctypes.c_int),
        ("sala_id", ctypes.c_int),
        ("horario_id", ctypes.c_int),
        ("score", ctypes.c_double),
    ]
```

## 3. Safe Wrapper Pattern with Context Management

Encapsulate C library interactions inside a Python service with guaranteed cleanup:

```python
from contextlib import contextmanager

class MotorAlocacaoBridge:
    def __init__(self, so_path: str):
        self.lib = ctypes.CDLL(so_path)
        self._configurar_assinaturas()

    def _configurar_assinaturas(self):
        self.lib.obter_versao_motor.restype = ctypes.c_char_p
        self.lib.obter_versao_motor.argtypes = []

        self.lib.liberar_memoria_alocacao.restype = None
        self.lib.liberar_memoria_alocacao.argtypes = [ctypes.c_void_p]

    def obter_versao(self) -> str:
        return self.lib.obter_versao_motor().decode("utf-8")
```

## 4. Signal & Segfault Handling

- Compile C shared libraries with `-Wall -Wextra -Werror -fPIC -shared`.
- In test environments, run Python under `faulthandler.enable()` to get a clean C stack trace in case of illegal memory access.
