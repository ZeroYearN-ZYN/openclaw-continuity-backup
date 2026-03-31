#!/usr/bin/env python3
"""
CHO细胞密码子优化器
Codon Optimizer for CHO Cells (Chinese Hamster Ovary)

功能：
- 根据CHO细胞的密码子偏好性进行优化
- 支持DNA/RNA序列输入
- 输出优化后的DNA序列
- 提供优化报告

参考数据来源：
- Kazusa Codon Usage Database (CHO细胞)
- literature: Lee et al., 2019
"""

import argparse
import json
from collections import defaultdict
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


# ============================================================================
# CHO 细胞密码子使用频率表 ( codon usage frequency per thousand)
# 数据来源: Kazusa Codon Usage Database - Cricetulus griseus (CHO细胞)
# ============================================================================
CHO_CODON_FREQ = {
    # Phenylalanine (F)
    'TTT': 16.3, 'TTC': 22.5,
    # Leucine (L)
    'TTA': 7.2,  'TTG': 13.4, 'CTT': 12.1, 'CTC': 23.4,
    'CTA': 7.8,  'CTG': 40.2,
    # Isoleucine (I)
    'ATT': 15.2, 'ATC': 24.3, 'ATA': 6.5,
    # Methionine (M) - Start
    'ATG': 22.5,
    # Valine (V)
    'GTT': 10.2, 'GTC': 16.8, 'GTA': 7.2, 'GTG': 28.4,
    # Serine (S)
    'TCT': 14.5, 'TCC': 20.2, 'TCA': 11.8, 'TCG': 4.2,
    'AGT': 13.5, 'AGC': 21.4,
    # Proline (P)
    'CCT': 16.8, 'CCC': 22.5, 'CCA': 15.2, 'CCG': 7.8,
    # Threonine (T)
    'ACT': 13.2, 'ACC': 24.5, 'ACA': 12.1, 'ACG': 6.2,
    # Alanine (A)
    'GCT': 15.8, 'GCC': 28.4, 'GCA': 15.2, 'GCG': 7.5,
    # Tyrosine (Y)
    'TAT': 12.1, 'TAC': 18.4,
    # Histidine (H)
    'CAT': 10.8, 'CAC': 15.2,
    # Glutamine (Q)
    'CAA': 12.5, 'CAG': 28.4,
    # Asparagine (N)
    'AAT': 14.2, 'AAC': 20.5,
    # Lysine (K)
    'AAA': 22.5, 'AAG': 35.2,
    # Aspartic Acid (D)
    'GAT': 16.5, 'GAC': 25.2,
    # Glutamic Acid (E)
    'GAA': 22.5, 'GAG': 32.5,
    # Cysteine (C)
    'TGT': 8.5,  'TGC': 12.5,
    # Tryptophan (W)
    'TGG': 15.2,
    # Arginine (R)
    'CGT': 8.2,  'CGC': 18.5, 'CGA': 11.2, 'CGG': 20.5,
    'AGA': 12.5, 'AGG': 21.4,
    # Glycine (G)
    'GGT': 12.5, 'GGC': 24.5, 'GGA': 18.5, 'GGG': 14.2,
}

# 标准遗传密码映射
CODON_TO_AA = {
    'TTT': 'F', 'TTC': 'F', 'TTA': 'L', 'TTG': 'L',
    'CTT': 'L', 'CTC': 'L', 'CTA': 'L', 'CTG': 'L',
    'ATT': 'I', 'ATC': 'I', 'ATA': 'I', 'ATG': 'M',
    'GTT': 'V', 'GTC': 'V', 'GTA': 'V', 'GTG': 'V',
    'TCT': 'S', 'TCC': 'S', 'TCA': 'S', 'TCG': 'S',
    'CCT': 'P', 'CCC': 'P', 'CCA': 'P', 'CCG': 'P',
    'ACT': 'T', 'ACC': 'T', 'ACA': 'T', 'ACG': 'T',
    'GCT': 'A', 'GCC': 'A', 'GCA': 'A', 'GCG': 'A',
    'TAT': 'Y', 'TAC': 'Y', 'TAA': '*', 'TAG': '*',
    'CAT': 'H', 'CAC': 'H', 'CAA': 'Q', 'CAG': 'Q',
    'AAT': 'N', 'AAC': 'N', 'AAA': 'K', 'AAG': 'K',
    'GAT': 'D', 'GAC': 'D', 'GAA': 'E', 'GAG': 'E',
    'TGT': 'C', 'TGC': 'C', 'TGA': '*', 'TGG': 'W',
    'CGT': 'R', 'CGC': 'R', 'CGA': 'R', 'CGG': 'R',
    'AGT': 'S', 'AGC': 'S', 'AGA': 'R', 'AGG': 'R',
    'GGT': 'G', 'GGC': 'G', 'GGA': 'G', 'GGG': 'G',
}

# 逆向映射：氨基酸 -> 同义密码子列表（按CHO偏好排序）
AA_TO_CODONS = defaultdict(list)
for codon, aa in CODON_TO_AA.items():
    AA_TO_CODONS[aa].append(codon)

# 对每个氨基酸的密码子按CHO频率排序（从高到低）
for aa in AA_TO_CODONS:
    AA_TO_CODONS[aa].sort(key=lambda c: CHO_CODON_FREQ.get(c, 0), reverse=True)


@dataclass
class OptimizationResult:
    """优化结果"""
    original_seq: str
    optimized_seq: str
    protein_seq: str
    gc_content_original: float
    gc_content_optimized: float
    cai_original: float
    cai_optimized: float
    changes: List[Dict]
    codon_usage_report: Dict


class CHOOptimizer:
    """CHO细胞密码子优化器"""

    def __init__(self, strategy: str = 'high'):
        """
        初始化优化器

        Args:
            strategy: 优化策略
                - 'highest': 总是使用最高频密码子
                - 'high': 使用高频密码子，避免连续相同密码子
                - 'balanced': 平衡考虑频率和mRNA稳定性
        """
        self.strategy = strategy

    def dna_to_protein(self, seq: str) -> str:
        """DNA序列转蛋白质序列"""
        seq = seq.upper().replace('U', 'T')
        protein = []

        for i in range(0, len(seq) - 2, 3):
            codon = seq[i:i+3]
            if len(codon) == 3 and codon in CODON_TO_AA:
                aa = CODON_TO_AA[codon]
                if aa == '*':
                    break  # 遇到终止密码子
                protein.append(aa)

        return ''.join(protein)

    def calculate_gc_content(self, seq: str) -> float:
        """计算GC含量"""
        seq = seq.upper()
        gc = sum(1 for n in seq if n in 'GC')
        return (gc / len(seq) * 100) if seq else 0

    def calculate_cai(self, seq: str) -> float:
        """计算密码子适应指数 (Codon Adaptation Index)"""
        seq = seq.upper()
        freq_sum = 0
        count = 0

        for i in range(0, len(seq) - 2, 3):
            codon = seq[i:i+3]
            if len(codon) == 3 and codon in CHO_CODON_FREQ:
                freq_sum += CHO_CODON_FREQ[codon]
                count += 1

        return (freq_sum / count) if count > 0 else 0

    def optimize_codon(self, codon: str, prev_codon: str = None, next_codon: str = None) -> str:
        """
        优化单个密码子

        Args:
            codon: 原始密码子
            prev_codon: 前一个密码子
            next_codon: 后一个密码子
        """
        aa = CODON_TO_AA.get(codon.upper())
        if not aa or aa == '*':
            return codon

        candidates = AA_TO_CODONS[aa]

        if self.strategy == 'highest':
            # 总是使用最高频密码子
            return candidates[0]

        elif self.strategy == 'high':
            # 避免连续相同密码子
            best = candidates[0]
            if prev_codon and candidates[0] == prev_codon[-3:] and len(candidates) > 1:
                best = candidates[1]
            return best

        elif self.strategy == 'balanced':
            # 平衡策略：考虑频率 + 避免连续重复
            for c in candidates:
                if c == prev_codon and len(candidates) > 1:
                    continue
                if c == next_codon and len(candidates) > 2:
                    continue
                return c
            return candidates[0]

        return candidates[0]

    def optimize(self, dna_seq: str, start_codon: str = 'ATG') -> Tuple[str, OptimizationResult]:
        """
        优化DNA序列

        Args:
            dna_seq: 输入的DNA序列
            start_codon: 起始密码子（默认ATG）
        """
        # 清理序列
        seq = dna_seq.upper().replace(' ', '').replace('\n', '')
        seq = seq.replace('U', 'T')
        seq = ''.join(c for c in seq if c in 'ATGC')

        if len(seq) < 3:
            raise ValueError("序列太短，至少需要3个核苷酸")

        # 验证是3的倍数
        if len(seq) % 3 != 0:
            seq = seq[:len(seq) - len(seq) % 3]

        # 获取蛋白质序列
        protein = self.dna_to_protein(seq)

        # 优化密码子
        optimized = []
        changes = []
        prev_codon = None

        for i in range(0, len(seq), 3):
            codon = seq[i:i+3]
            next_codon = seq[i+3:i+6] if i + 3 < len(seq) else None

            # 起始密码子特殊处理
            if i == 0:
                optimized.append(start_codon)
                if codon != start_codon:
                    changes.append({
                        'position': 1,
                        'original': codon,
                        'optimized': start_codon,
                        'amino_acid': 'M'
                    })
            else:
                new_codon = self.optimize_codon(codon, prev_codon, next_codon)
                optimized.append(new_codon)

                if new_codon != codon:
                    aa = CODON_TO_AA.get(codon, '?')
                    changes.append({
                        'position': i // 3 + 1,
                        'original': codon,
                        'optimized': new_codon,
                        'amino_acid': aa
                    })

            prev_codon = codon

        optimized_seq = ''.join(optimized)

        # 计算统计
        gc_orig = self.calculate_gc_content(seq)
        gc_opt = self.calculate_gc_content(optimized_seq)
        cai_orig = self.calculate_cai(seq)
        cai_opt = self.calculate_cai(optimized_seq)

        # 生成密码子使用报告
        report = self._generate_codon_report(optimized_seq)

        return optimized_seq, OptimizationResult(
            original_seq=seq,
            optimized_seq=optimized_seq,
            protein_seq=protein,
            gc_content_original=gc_orig,
            gc_content_optimized=gc_opt,
            cai_original=cai_orig,
            cai_optimized=cai_opt,
            changes=changes,
            codon_usage_report=report
        )

    def _generate_codon_report(self, seq: str) -> Dict:
        """生成密码子使用报告"""
        usage = defaultdict(int)
        total = 0

        for i in range(0, len(seq) - 2, 3):
            codon = seq[i:i+3]
            if len(codon) == 3:
                usage[codon] += 1
                total += 1

        # 计算每个氨基酸的最优密码子使用率
        optimal_usage = {}
        for aa, codons in AA_TO_CODONS.items():
            optimal = codons[0]
            count = sum(usage[c] for c in codons if c in usage)
            optimal_count = usage.get(optimal, 0)
            optimal_usage[aa] = {
                'optimal_codon': optimal,
                'optimal_count': optimal_count,
                'total_count': count,
                'percentage': (optimal_count / count * 100) if count > 0 else 0
            }

        return {
            'total_codons': total,
            'codon_counts': dict(usage),
            'optimal_usage': optimal_usage
        }

    def print_report(self, result: OptimizationResult):
        """打印优化报告"""
        print("\n" + "=" * 70)
        print("                    CHO 细胞密码子优化报告")
        print("=" * 70)

        print(f"\n📊 序列统计:")
        print(f"   原始序列长度: {len(result.original_seq)} bp")
        print(f"   优化序列长度: {len(result.optimized_seq)} bp")
        print(f"   蛋白质长度: {len(result.protein_seq)} aa")

        print(f"\n📈 优化效果:")
        print(f"   GC含量: {result.gc_content_original:.1f}% → {result.gc_content_optimized:.1f}%")
        print(f"   CAI: {result.cai_original:.2f} → {result.cai_optimized:.2f}")
        print(f"   密码子替换数: {len(result.changes)}")

        if result.changes:
            print(f"\n🔄 关键替换 (前10个):")
            print(f"   位置  原始    优化    氨基酸")
            print(f"   " + "-" * 35)
            for change in result.changes[:10]:
                print(f"   {change['position']:4d}  {change['original']}  →  {change['optimized']}    {change['amino_acid']}")

            if len(result.changes) > 10:
                print(f"   ... 还有 {len(result.changes) - 10} 处替换")

        print(f"\n🧬 最优密码子使用率:")
        for aa, data in sorted(result.codon_usage_report['optimal_usage'].items()):
            bar_len = int(data['percentage'] / 5)
            bar = '█' * bar_len + '░' * (20 - bar_len)
            print(f"   {aa}: [{bar}] {data['percentage']:.1f}%")

        print(f"\n💾 优化后序列:")
        print(f"   {result.optimized_seq[:60]}...")

        print("\n" + "=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description='CHO细胞密码子优化器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s input.fasta -o optimized.fasta
  %(prog)s "ATGGCCTACGAC" --report
  %(prog)s seq.txt --strategy balanced --output result.txt
        """
    )

    parser.add_argument('input', nargs='?', help='输入文件或DNA序列')
    parser.add_argument('-o', '--output', help='输出文件路径')
    parser.add_argument('--strategy', choices=['highest', 'high', 'balanced'],
                        default='high', help='优化策略')
    parser.add_argument('--start-codon', default='ATG', help='起始密码子')
    parser.add_argument('--report', action='store_true', help='打印详细报告')
    parser.add_argument('--json', action='store_true', help='输出JSON格式')

    args = parser.parse_args()

    # 读取输入
    if args.input and ('ATGC' in args.input.upper() or 'U' in args.input.upper()):
        # 直接输入序列
        dna_seq = args.input
    elif args.input:
        # 从文件读取
        try:
            with open(args.input, 'r') as f:
                content = f.read()
                # 尝试从FASTA格式提取
                if content.startswith('>'):
                    lines = content.strip().split('\n')
                    dna_seq = ''.join(line for line in lines if not line.startswith('>'))
                else:
                    dna_seq = content.replace('\n', '').replace(' ', '')
        except FileNotFoundError:
            print(f"错误: 找不到文件 {args.input}")
            return 1
    else:
        parser.print_help()
        return 1

    # 执行优化
    optimizer = CHOOptimizer(strategy=args.strategy)
    optimized_seq, result = optimizer.optimize(dna_seq, start_codon=args.start_codon)

    # 输出结果
    if args.json:
        output = {
            'original_seq': result.original_seq,
            'optimized_seq': result.optimized_seq,
            'protein_seq': result.protein_seq,
            'gc_content': {
                'original': round(result.gc_content_original, 2),
                'optimized': round(result.gc_content_optimized, 2)
            },
            'cai': {
                'original': round(result.cai_original, 2),
                'optimized': round(result.cai_optimized, 2)
            },
            'changes': result.changes,
            'strategy': args.strategy
        }
        print(json.dumps(output, indent=2))
    else:
        if args.report:
            optimizer.print_report(result)
        else:
            print(optimized_seq)

    # 保存文件
    if args.output:
        with open(args.output, 'w') as f:
            f.write(optimized_seq)
        print(f"✅ 已保存到: {args.output}")

    return 0


if __name__ == '__main__':
    exit(main())
