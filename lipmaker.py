import ast
import json
import re
import zipfile
from pathlib import Path
# ============================================================
# الإعدادات
# ============================================================
# المجلد الذي توجد بداخله ملفات .whl
WHEELS_DIR = Path(
    r"J:\System\Programing_Projects\Prog_Bock\static\JeeBlocks\languages\python\Lib"
)
# ملف أسماء المكتبات التي تم تنزيلها
LIBRARIES_LIST = Path(
    r"J:\System\Programing_Projects\Prog_Bock\static\JeeBlocks\languages\python\Lib\all.txt"
)
# ملف JSON الناتج
OUTPUT_FILE = Path(
    r"J:\System\Programing_Projects\Prog_Bock\libraries.json"
)
# ============================================================
# قراءة أسماء المكتبات
# ============================================================
def read_library_names(file_path):
    libraries = []
    if not file_path.exists():
        print("❌ ملف أسماء المكتبات غير موجود:")
        print(file_path)
        return libraries
    with file_path.open(
        "r",
        encoding="utf-8",
        errors="ignore"
    ) as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            # تجاهل التعليقات
            if line.startswith("#"):
                continue
            # ------------------------------------------------
            # لو الملف فيه:
            #
            # pandas==2.3.1
            # numpy>=2.0
            # requests
            # ------------------------------------------------
            line = re.split(
                r"[<>=!~]",
                line,
                maxsplit=1
            )[0]
            line = line.strip()
            if line:
                libraries.append(line)
    # إزالة التكرار
    libraries = list(
        dict.fromkeys(libraries)
    )
    return libraries
# ============================================================
# تحويل اسم المكتبة إلى اسم مناسب للبحث داخل WHL
# ============================================================
def normalize_name(name):
    return re.sub(
        r"[-_.]+",
        "-",
        name
    ).lower()
# ============================================================
# استخراج اسم المكتبة من اسم WHL
#
# مثال:
#
# pandas-2.3.1-cp312-cp312-win_amd64.whl
#
# يصبح:
#
# pandas
# ============================================================
def wheel_distribution_name(wheel_name):
    name = Path(
        wheel_name
    ).name
    if not name.endswith(".whl"):
        return ""
    name = name[:-4]
    parts = name.split("-")
    if not parts:
        return ""
    return parts[0]
# ============================================================
# إنشاء Index لملفات WHL
# ============================================================
def build_wheel_index():
    print()
    print("جاري فهرسة ملفات WHL...")
    index = {}
    wheels = list(
        WHEELS_DIR.glob("*.whl")
    )
    print(
        f"تم العثور على {len(wheels)} ملف WHL"
    )
    for wheel in wheels:
        name = wheel_distribution_name(
            wheel.name
        )
        if not name:
            continue
        normalized = normalize_name(
            name
        )
        # لو فيه أكثر من نسخة لنفس المكتبة
        # نحتفظ بكل النسخ
        index.setdefault(
            normalized,
            []
        ).append(wheel)
    return index
# ============================================================
# استخراج functions / classes من Python
# ============================================================
def extract_ast_items(source):
    items = set()
    try:
        tree = ast.parse(
            source
        )
    except Exception:
        return items
    for node in ast.walk(tree):
        # ----------------------------------------------------
        # function
        # ----------------------------------------------------
        if isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef
            )
        ):
            name = node.name
            if not name.startswith("_"):
                items.add(name)
        # ----------------------------------------------------
        # class
        # ----------------------------------------------------
        elif isinstance(
            node,
            ast.ClassDef
        ):
            name = node.name
            if not name.startswith("_"):
                items.add(name)
    return items
# ============================================================
# تحليل imports
# ============================================================
def extract_imports(source):
    modules = set()
    try:
        tree = ast.parse(
            source
        )
    except Exception:
        return modules
    for node in ast.walk(tree):
        # import numpy
        # import numpy.random
        if isinstance(
            node,
            ast.Import
        ):
            for alias in node.names:
                name = alias.name
                if name:
                    modules.add(name)
        # from numpy import array
        #
        # نضيف numpy
        # ونضيف numpy.array
        elif isinstance(
            node,
            ast.ImportFrom
        ):
            if node.module:
                module = node.module
                modules.add(
                    module
                )
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    if alias.name.startswith("_"):
                        continue
                    modules.add(
                        f"{module}.{alias.name}"
                    )
    return modules
# ============================================================
# تحويل مسار Python داخل WHL إلى module name
# ============================================================
def python_path_to_module(path):
    path = path.replace(
        "\\",
        "/"
    )
    if not path.endswith(".py"):
        return None
    parts = path.split("/")
    # تجاهل metadata
    if any(
        part.endswith(".dist-info")
        or part.endswith(".egg-info")
        for part in parts
    ):
        return None
    # حذف .py
    parts[-1] = parts[-1][:-3]
    # __init__.py
    if parts[-1] == "__init__":
        parts.pop()
    if not parts:
        return None
    # تجاهل private modules
    if any(
        part.startswith("_")
        for part in parts
    ):
        return None
    return ".".join(parts)
# ============================================================
# تحليل WHL
# ============================================================
def scan_wheel(wheel_path):
    result = set()
    try:
        with zipfile.ZipFile(
            wheel_path,
            "r"
        ) as archive:
            names = archive.namelist()
            for filename in names:
                if not filename.endswith(".py"):
                    continue
                module_name = python_path_to_module(
                    filename
                )
                if not module_name:
                    continue
                # --------------------------------------------
                # إضافة module
                # --------------------------------------------
                result.add(
                    module_name
                )
                try:
                    data = archive.read(
                        filename
                    )
                    source = data.decode(
                        "utf-8",
                        errors="ignore"
                    )
                except Exception:
                    continue
                # --------------------------------------------
                # functions/classes
                # --------------------------------------------
                items = extract_ast_items(
                    source
                )
                for item in items:
                    result.add(
                        f"{module_name}.{item}"
                    )
                # --------------------------------------------
                # imports
                # --------------------------------------------
                imports = extract_imports(
                    source
                )
                for item in imports:
                    result.add(item)
    except zipfile.BadZipFile:
        print(
            f"  ⚠️ ملف WHL تالف: {wheel_path.name}"
        )
    except Exception as e:
        print(
            f"  ⚠️ خطأ في {wheel_path.name}: {e}"
        )
    return result
# ============================================================
# اختيار أفضل WHL للمكتبة
# ============================================================
def find_wheel(
    library_name,
    wheel_index
):
    normalized = normalize_name(
        library_name
    )
    candidates = wheel_index.get(
        normalized,
        []
    )
    if not candidates:
        return None
    # لو عندنا أكثر من نسخة
    # نختار أول واحدة.
    #
    # يمكن لاحقًا تطويرها لاختيار
    # أحدث إصدار تلقائيًا.
    return candidates[0]
# ============================================================
# Main
# ============================================================
def main():
    print("=" * 70)
    print("WHL Python Library Scanner")
    print("=" * 70)
    print()
    print("📁 مجلد WHL:")
    print(WHEELS_DIR)
    print()
    print("📄 ملف المكتبات:")
    print(LIBRARIES_LIST)
    print()
    print("📦 ملف الناتج:")
    print(OUTPUT_FILE)
    # ========================================================
    # التحقق من المسارات
    # ========================================================
    if not WHEELS_DIR.exists():
        print()
        print("❌ مجلد WHL غير موجود!")
        return
    if not LIBRARIES_LIST.exists():
        print()
        print("❌ ملف أسماء المكتبات غير موجود!")
        return
    # ========================================================
    # قراءة المكتبات
    # ========================================================
    print()
    print("جاري قراءة أسماء المكتبات...")
    libraries = read_library_names(
        LIBRARIES_LIST
    )
    print(
        f"تم العثور على {len(libraries)} مكتبة في الملف."
    )
    # ========================================================
    # فهرسة WHL
    # ========================================================
    wheel_index = build_wheel_index()
    # ========================================================
    # إنشاء قاعدة البيانات
    # ========================================================
    database = []
    found = 0
    not_found = 0
    print()
    print("=" * 70)
    print("بدء تحليل المكتبات")
    print("=" * 70)
    for index, library in enumerate(
        libraries,
        1
    ):
        print(
            f"[{index}/{len(libraries)}] {library}",
            end=" "
        )
        wheel = find_wheel(
            library,
            wheel_index
        )
        # ----------------------------------------------------
        # لم يتم العثور على WHL
        # ----------------------------------------------------
        if wheel is None:
            print("❌ WHL غير موجود")
            database.append(
                {
                    library: []
                }
            )
            not_found += 1
            continue
        # ----------------------------------------------------
        # تحليل WHL
        # ----------------------------------------------------
        print(
            f"→ {wheel.name}"
        )
        items = scan_wheel(
            wheel
        )
        database.append(
            {
                library: sorted(items)
            }
        )
        found += 1
    # ========================================================
    # حفظ JSON
    # ========================================================
    print()
    print("=" * 70)
    print("جاري حفظ libraries.json ...")
    print("=" * 70)
    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            database,
            file,
            ensure_ascii=False,
            indent=4
        )
    # ========================================================
    # النتيجة
    # ========================================================
    print()
    print("=" * 70)
    print("✅ انتهى الفحص")
    print("=" * 70)
    print()
    print(
        f"📚 المكتبات في ملف الأسماء : {len(libraries)}"
    )
    print(
        f"✅ تم العثور على WHL       : {found}"
    )
    print(
        f"❌ لم يتم العثور على WHL   : {not_found}"
    )
    print()
    print("📄 الملف الناتج:")
    print(
        OUTPUT_FILE.absolute()
    )
# ============================================================
# تشغيل
# ============================================================
if __name__ == "__main__":
    main()