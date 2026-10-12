"""
生成可训练数据集，完全复用render_samples.py渲染逻辑，保证渲染行为与核验样张完全一致
输出: train / val_graph / val_select / test，附带meta数据集清单
"""
import json
import random
from pathlib import Path
from render_samples import (
    ROOT, checked_input, common_layout, render_high, blur_white, save_json
)

# --------------------------配置--------------------------
OUT_ROOT = ROOT / "dataset_81"
SPLITS = ["train", "val_graph", "val_select", "test"]
SAMPLE_PER_CHAR = {
    "train": 20,
    "val_graph": 8,
    "val_select": 6,
    "test": 6
}
SIGMAS = [0.0, 0.5, 1.0]
OFFSET_LIMIT = (-3.0, 3.0)  # dx,dy 输出像素单位
RANDOM_SEED = 42
SIZE = 64
SCALE = 4
# ---------------------------------------------------------

def main():
    random.seed(RANDOM_SEED)
    data, _ = checked_input()
    char_entries = data["characters"]
    char_list = [c["char"] for c in char_entries]
    char_to_entry = {c["char"]: c for c in char_entries}
    print(f"总字符数 {len(char_entries)}")

    # ===== 完全复用原始脚本：全局共同font、baseline、union bbox =====
    font, font_size, union_bbox, baseline_high = common_layout(char_list)

    # 创建输出目录
    meta_dir = OUT_ROOT / "meta"
    for sp in SPLITS:
        (OUT_ROOT / sp).mkdir(parents=True, exist_ok=True)
    meta_dir.mkdir(exist_ok=True)

    all_meta_records = []

    for entry in char_entries:
        ch = entry["char"]
        cid = entry["class_id"]
        total_need = sum(SAMPLE_PER_CHAR.values())

        # 生成该字符全部随机条件
        cond_pool = []
        for _ in range(total_need):
            dx_out = random.uniform(*OFFSET_LIMIT)
            dy_out = random.uniform(*OFFSET_LIMIT)
            sigma = random.choice(SIGMAS)
            cond_pool.append((dx_out, dy_out, sigma))

        ptr = 0
        for split_name in SPLITS:
            n_sample = SAMPLE_PER_CHAR[split_name]
            batch_cond = cond_pool[ptr:ptr + n_sample]
            ptr += n_sample

            for dx_out, dy_out, sigma in batch_cond:
                # 调用原版render_high，和样张渲染逻辑完全相同
                img_high, _, cropped_flag = render_high(
                    char=ch,
                    font=font,
                    baseline=baseline_high,
                    dx=dx_out,
                    dy=dy_out
                )
                if cropped_flag:
                    raise RuntimeError(f"字符 {ch} 渲染发生裁切！")

                # 下采样到64
                img_64 = img_high.resize((SIZE, SIZE), resample=Image.Resampling.LANCZOS)
                # 原版模糊函数：带16px白边padding
                img_blur = blur_white(img_64, sigma)

                fname = f"cid_{cid}_{len(all_meta_records):06d}.png"
                save_path = OUT_ROOT / split_name / fname
                img_blur.save(save_path)

                rec = {
                    "char": ch,
                    "class_id": cid,
                    "split": split_name,
                    "dx_out": round(dx_out, 2),
                    "dy_out": round(dy_out, 2),
                    "sigma": sigma,
                    "filename": fname,
                    "file_relative": f"{split_name}/{fname}"
                }
                all_meta_records.append(rec)

                if len(all_meta_records) % 200 == 0:
                    print(f"已渲染 {len(all_meta_records)}")

    # 保存元数据
    meta_json = meta_dir / "dataset_meta.json"
    save_json(meta_json, all_meta_records)

    print("\n==== 数据集生成完成 ====")
    print(f"输出根目录: {OUT_ROOT.resolve()}")
    for k, v in SAMPLE_PER_CHAR.items():
        print(f"  {k}: 每字符 {v} 张")
    print(f"元数据清单: {meta_json.resolve()}")


if __name__ == "__main__":
    from PIL import Image
    main()
