import os
import sys
import typing
import tempfile
import shutil
import preppipe
import preppipe.pipeline_cmd
import preppipe.pipeline
import preppipe.language
import warnings
import itertools
import pytest

# pylint: disable=wrong-import-position

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
import util


def renpy_handle_test_input(inputfile : str, lang : str, assetdir: str, dirname: str, skipOutputCheck : bool) -> None:
  # 给每个语言模式都测试一下
  filebase, ext = os.path.splitext(inputfile)
  input_flag = None
  if ext == ".odt":
    # 找到了个样例
    input_flag = "--odf"
  elif ext == ".docx":
    input_flag = "--docx"
  elif ext == ".txt" and filebase.split('_')[-1] in ("utf8", "gb2312"):
    input_flag = "--txt"
  elif ext == ".md":
    input_flag = "--md"
  if input_flag is None:
    raise RuntimeError(f"Unsupported file extension {ext} for file {inputfile}")
  with tempfile.TemporaryDirectory() as project_dir:
    testpath = os.path.join(project_dir, f"{filebase}_{input_flag.lstrip('--')}_{lang}_renpy_test")
    shutil.rmtree(testpath, ignore_errors=True)
    preppipe.language.Translatable.language_update_preferred_langs([lang])
    args = [# "-v",
            "--searchpath", assetdir,
            input_flag, os.path.join(dirname, inputfile),
            "--cmdsyntax", "--vnparse", "--vncodegen",
            "--vn-blocksorting", "--vn-entryinference", "--vn-longsaysplitting",
            "--renpy-codegen",
            "--renpy-export", testpath]
    preppipe.pipeline.pipeline_main(args)
    strdump = util.collectDirectoryDataAsText(testpath, excludepatterns=[
      "preppipert.rpy",
      ".preppipe_export_cache.json",
    ])
    # print(strdump)
    # 如有需要就输出
    util.copyTestDirIfRequested(testpath, "e2e_renpy")
    # 再取已保存的内容
    # 如果我们还没保存内容，那么这是第一次运行，只记录
    expected_content = ""
    filerootbase = filebase.split('_')[0]
    expected_path = os.path.join(dirname, filerootbase + '_' + lang +".txt")
    if os.path.exists(expected_path):
      with open(expected_path, "r", encoding="utf-8") as f:
        expected_content = f.read()
    else:
      with open(expected_path, "w", encoding="utf-8") as f:
        f.write(strdump)
      expected_content = strdump
    if not skipOutputCheck:
      expected_content_lines = expected_content.splitlines()
      strdump_lines = strdump.splitlines()
      for linecnt in range(len(expected_content.splitlines())):
        if linecnt >= len(strdump_lines):
          raise RuntimeError(f"Output file {expected_path} is shorter than expected, missing line {linecnt + 1}")
        expected = expected_content_lines[linecnt]
        actual = strdump_lines[linecnt]
        if expected != actual:
          if "<NO_CHECK>" in expected:
            # 如果有 NO_CHECK 标记，我们比较去掉它之后的内容
            expected_fragments = expected.split("<NO_CHECK>")
            cur_pos = 0
            matched = True
            for fragment in expected_fragments:
              found_pos = actual.find(fragment, cur_pos)
              if found_pos < 0:
                matched = False
                break
              cur_pos = found_pos + len(fragment)
            if matched:
              continue
          raise RuntimeError(f"Output file {expected_path} differs at line {linecnt + 1}: expected '{expected}', got '{actual}'")
      for linecnt in range(len(expected_content_lines), len(strdump_lines)):
        actual = strdump_lines[linecnt]
        raise RuntimeError(f"Output file {expected_path} has extra line {linecnt + 1}: '{actual}'")

filesSkipOutputCheck = [
]

inputfiles = [
  "zh1.docx",
  "zh1.odt",
  "zh1_utf8.txt",
  "zh1_gb2312.txt",
  "zh1.md",
  "zh2.docx",
  "zh2.odt",
  "zh3.docx",
  "zh3.odt",
  "zh3.md",
  "zh4.docx",
  "zh4.odt",
  "zh4.md",
  "demo.docx",
  "demo.odt",
  *filesSkipOutputCheck,
]

langs = [
  "zh_cn",
  "zh_hk",
]

@pytest.mark.parametrize("inputfile, lang", list(itertools.product(inputfiles, langs)))
def test_zh(inputfile, lang):
  assetdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "assets")
  dirname = os.path.join(os.path.dirname(os.path.realpath(__file__)), "zh")
  renpy_handle_test_input(
    inputfile = inputfile,
    lang = lang,
    assetdir = assetdir,
    dirname = dirname,
    skipOutputCheck = (inputfile in filesSkipOutputCheck)
  )
