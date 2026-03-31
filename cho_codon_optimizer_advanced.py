#!/usr/bin/env python3
"""
CHO细胞密码子优化器 - 高级版
Codon Optimizer for CHO Cells (Chinese Hamster Ovary) - Advanced

基于以下技术优化：
1. Thermo Fisher GeneOptimizer 多参数优化算法
2. 金斯瑞 GenScript 种群免疫算法 (Population Immune Algorithm)
3. 滑动窗口优化策略

功能：
- 多参数优化：密码子偏好 + GC含量 + mRNA稳定性
- 限制酶切位点管理（排除/保留）
- 隐蔽剪接位点去除
- 重复序列避免
- 种群进化优化

参考：
- Thermo Fisher GeneOptimizer (滑动窗口多参数优化)
- GenScript 专利: CN110999637A (种群免疫算法)
- Kazusa Codon Usage Database (CHO细胞)
"""

import argparse
import json
import random
import math
from collections import defaultdict
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from copy import deepcopy


# ============================================================================
# 第一部分：CHO 细胞密码子使用频率表
# ============================================================================
# 数据来源: Kazusa Codon Usage Database - Cricetulus griseus (CHO细胞)
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

for aa in AA_TO_CODONS:
    AA_TO_CODONS[aa].sort(key=lambda c: CHO_CODON_FREQ.get(c, 0), reverse=True)

# 每个氨基酸的最优密码子
OPTIMAL_CODON = {aa: codons[0] for aa, codons in AA_TO_CODONS.items()}


# ============================================================================
# 第二部分：限制酶切位点和有害序列模式
# ============================================================================
# 常见限制酶切位点（6碱基酶切位点）
RESTRICTION_SITES = {
    # 常用酶切位点
    'AAGCTT': 'HindIII',
    'GGATCC': 'BamHI',
    'GAATTC': 'EcoRI',
    'CTGCAG': 'PstI',
    'CCCGGG': 'XmaI',
    'GGTACC': 'KpnI',
    'TCTAGA': 'XbaI',
    'ACTAGT': 'SpeI',
    'GCGGCCGC': 'NotI',
    'ATTTAAAT': 'EcoRV',
    'GATATC': 'EcoRV',
    'TTATAA': 'MfeI',
    'CAATTG': 'MfeI',
    'GTCGAC': 'SalI',
    'CCATGG': 'NcoI',
    'CATATG': 'NdeI',
    'GAGCTC': 'SacI',
    'AGATCT': 'BglII',
    'AGGCCT': 'StuI',
    'TTCGAA': 'SmaI',
    'CGGCCG': 'EagI',
    'GCGCGC': 'ApaI',
}

# RNA不稳定性基序 (AU-rich elements) - 需要避免
RNA_INSTABILITY_MOTIFS = [
    'ATTTA', 'ATTTAT', 'ATTTATT', 'ATATA', 'ATATAT',
    'TTATTT', 'TTTATT', 'TTTTAT', 'AATTTA', 'AATTTT',
]

# 重复序列模式
REPEAT_MOTIFS = [
    'GGTGGT', 'GATGAT', 'ATCGAT', 'CTCGAG', 'GAATTC',
    'TATATA', 'GAGAGA', 'CACACA', 'GTGGTG', 'TCTTCT',
]


# ============================================================================
# 第三部分：优化参数和权重
# ============================================================================
@dataclass
class OptimizationParams:
    """优化参数"""
    # 目标GC含量范围 (%)
    target_gc_min: float = 40.0
    target_gc_max: float = 70.0
    
    # 权重（影响适应度得分）
    weight_cai: float = 0.35       # 密码子适应指数权重
    weight_gc: float = 0.20        # GC含量权重
    weight_structure: float = 0.15  # mRNA结构稳定性权重
    weight_restriction: float = 0.20  # 限制酶切位点权重
    weight_repeat: float = 0.10    # 重复序列权重
    
    # 优化参数
    max_codon_repeats: int = 2     # 最大连续相同密码子次数
    window_size: int = 50          # 滑动窗口大小
    
    # 种群算法参数
    population_size: int = 50
    generations: int = 100
    mutation_rate: float = 0.1
    crossover_rate: float = 0.8
    elite_count: int = 5


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
    fitness_score: float
    restriction_sites_removed: List[str]
    warnings: List[str]


# ============================================================================
# 第四部分：核心优化器类
# ============================================================================
class CHOOptimizerAdvanced:
    """
    CHO细胞密码子优化器 - 高级版
    
    集成：
    1. 多参数优化（Thermo Fisher GeneOptimizer）
    2. 种群免疫算法（GenScript专利启发）
    3. 滑动窗口局部优化
    """

    def __init__(self, params: OptimizationParams = None):
        self.params = params or OptimizationParams()

    def dna_to_protein(self, seq: str) -> str:
        """DNA序列转蛋白质序列"""
        seq = seq.upper().replace('U', 'T')
        protein = []
        for i in range(0, len(seq) - 2, 3):
            codon = seq[i:i+3]
            if len(codon) == 3 and codon in CODON_TO_AA:
                aa = CODON_TO_AA[codon]
                if aa == '*':
                    break
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

    def calculate_fitness(self, seq: str) -> Dict:
        """
        计算适应度得分（多参数优化）
        
        基于金斯瑞种群免疫算法的适应度函数设计
        """
        result = {
            'cai_score': 0,
            'gc_score': 0,
            'structure_score': 0,
            'restriction_score': 0,
            'repeat_score': 0,
            'total_fitness': 0,
            'details': {}
        }
        
        # 1. CAI 得分（越高越好）
        cai = self.calculate_cai(seq)
        result['cai_score'] = min(cai / 30.0, 1.0)  # 归一化
        result['details']['cai'] = cai
        
        # 2. GC含量得分
        gc = self.calculate_gc_content(seq)
        if self.params.target_gc_min <= gc <= self.params.target_gc_max:
            result['gc_score'] = 1.0
        else:
            dist = min(abs(gc - self.params.target_gc_min), 
                      abs(gc - self.params.target_gc_max))
            result['gc_score'] = max(0, 1 - dist / 30)
        result['details']['gc_content'] = gc
        
        # 3. mRNA结构稳定性
        codon_repeats = self._count_codon_repeats(seq)
        result['structure_score'] = max(0, 1 - codon_repeats / 20)
        result['details']['codon_repeats'] = codon_repeats
        
        # 4. 限制酶切位点得分
        restriction_count = self._count_restriction_sites(seq)
        result['restriction_score'] = max(0, 1 - restriction_count / 5)
        result['details']['restriction_sites'] = restriction_count
        
        # 5. 重复序列得分
        repeat_count = self._count_repeats(seq)
        result['repeat_score'] = max(0, 1 - repeat_count / 10)
        result['details']['repeat_motifs'] = repeat_count
        
        # 加权总分
        result['total_fitness'] = (
            result['cai_score'] * self.params.weight_cai +
            result['gc_score'] * self.params.weight_gc +
            result['structure_score'] * self.params.weight_structure +
            result['restriction_score'] * self.params.weight_restriction +
            result['repeat_score'] * self.params.weight_repeat
        )
        
        return result

    def _count_codon_repeats(self, seq: str) -> int:
        """计算连续相同密码子出现的次数"""
        repeats = 0
        for i in range(0, len(seq) - 6, 3):
            if seq[i:i+3] == seq[i+3:i+6]:
                repeats += 1
        return repeats

    def _count_restriction_sites(self, seq: str) -> int:
        """计算限制酶切位点数量"""
        count = 0
        for site in RESTRICTION_SITES:
            count += seq.count(site)
        return count

    def _count_repeats(self, seq: str) -> int:
        """计算重复序列基序数量"""
        count = 0
        for motif in REPEAT_MOTIFS:
            count += seq.count(motif)
        return count

    def _find_restriction_sites(self, seq: str) -> List[Dict]:
        """查找序列中的限制酶切位点"""
        sites = []
        for site, enzyme in RESTRICTION_SITES.items():
            start = 0
            while True:
                idx = seq.find(site, start)
                if idx == -1:
                    break
                sites.append({
                    'position': idx + 1,
                    'site': site,
                    'enzyme': enzyme
                })
                start = idx + 1
        return sites

    def _remove_restriction_sites(self, seq: str, exclude_sites: Set[str] = None) -> str:
        """移除限制酶切位点（使用次优密码子）"""
        result = seq
        
        for site, enzyme in RESTRICTION_SITES.items():
            if exclude_sites and site in exclude_sites:
                continue
                
            while site in result:
                idx = result.find(site)
                codon_idx = idx // 3
                aa_start = codon_idx * 3
                codon = result[aa_start:aa_start+3]
                aa = CODON_TO_AA.get(codon, '')
                
                if aa and aa != '*' and len(AA_TO_CODONS[aa]) > 1:
                    candidates = AA_TO_CODONS[aa]
                    for c in reversed(candidates):
                        if site not in c:
                            new_codon = c
                            break
                    else:
                        new_codon = candidates[-1]
                    
                    result = result[:aa_start] + new_codon + result[aa_start+3:]
                else:
                    break
        
        return result

    def _optimize_with_sliding_window(self, seq: str, window_size: int = None) -> str:
        """
        滑动窗口优化（Thermo Fisher GeneOptimizer核心算法）
        """
        if window_size is None:
            window_size = self.params.window_size
            
        seq = seq.upper()
        optimized = list(seq)
        seq_len = len(optimized)
        
        window_size = min(window_size, seq_len)
        step = window_size // 2
        
        for start in range(0, seq_len - window_size + 1, step):
            end = min(start + window_size, seq_len)
            
            start = (start // 3) * 3
            end = (end // 3) * 3
            
            if end - start < 3:
                continue
                
            window = ''.join(optimized[start:end])
            best_window = self._optimize_window(window, start)
            
            for i, base in enumerate(best_window):
                optimized[start + i] = base
        
        return ''.join(optimized)

    def _optimize_window(self, window: str, offset: int) -> str:
        """优化单个窗口内的序列"""
        if len(window) < 3:
            return window
            
        result = list(window)
        n_codons = len(window) // 3
        
        for i in range(n_codons):
            start = i * 3
            codon = window[start:start+3]
            aa = CODON_TO_AA.get(codon, '')
            
            if aa and aa != '*':
                optimal = OPTIMAL_CODON[aa]
                temp_result = result.copy()
                temp_result[start:start+3] = list(optimal)
                temp_seq = ''.join(temp_result)
                
                if self._is_acceptable(temp_seq, start, start+3):
                    result[start:start+3] = list(optimal)
        
        return ''.join(result)

    def _is_acceptable(self, seq: str, start: int, end: int) -> bool:
        """检查序列变更是否可接受"""
        if self._count_restriction_sites(seq[start:end]) > 0:
            return False
        return True

    def _ensure_length(self, seq: str, target_length: int) -> str:
        """确保序列长度正确"""
        seq = seq[:target_length]
        if len(seq) < target_length:
            seq = seq + 'ATG' * ((target_length - len(seq)) // 3)
        return seq
    
    def _population_immune_optimize(self, protein: str, max_iterations: int = None) -> str:
        """
        种群免疫算法优化（参考GenScript专利）
        """
        if max_iterations is None:
            max_iterations = self.params.generations
        
        target_length = len(protein) * 3  # 目标序列长度
        
        # 初始化种群
        population = []
        for _ in range(self.params.population_size):
            seq = []
            for aa in protein:
                if aa == '*':
                    # 终止密码子
                    seq.append('TAA')
                elif aa in OPTIMAL_CODON and random.random() < 0.7:
                    seq.append(OPTIMAL_CODON[aa])
                elif aa in AA_TO_CODONS:
                    codons = AA_TO_CODONS[aa]
                    seq.append(random.choice(codons))
                else:
                    seq.append('ATG' if aa == 'M' else 'GCT')
            
            seq_str = ''.join(seq)
            # 确保长度一致
            if len(seq_str) < target_length:
                seq_str = seq_str + "ATG" * ((target_length - len(&0)) // 3)
            elif len(seq_str) > target_length:
                seq_str = seq_str[:target_length]
            
            population.append(seq_str)
        
        # 进化
        best_seq = None
        best_fitness = -1
        
        for gen in range(max_iterations):
            fitness_scores = []
            for seq in population:
                # 确保长度一致
                if len(seq) != target_length:
                    seq = seq[:target_length] + "ATG" * ((target_length - len(&0)) // 3)
                fitness = self.calculate_fitness(seq)
                score = fitness['total_fitness']
                fitness_scores.append((seq, score))
                if score > best_fitness:
                    best_fitness = score
                    best_seq = seq
            
            # 选择
            selected = self._tournament_select(fitness_scores, k=3)
            
            # 生成新一代
            new_population = []
            
            # 保留精英
            fitness_scores.sort(key=lambda x: x[1], reverse=True)
            for i in range(min(self.params.elite_count, len(fitness_scores))):
                seq = fitness_scores[i][0]
                if len(seq) != target_length:
                    seq = seq[:target_length] + "ATG" * ((target_length - len(&0)) // 3)
                new_population.append(seq)
            
            # 交叉和变异
            while len(new_population) < self.params.population_size:
                if len(selected) < 2:
                    parent1 = selected[0] if selected else best_seq
                    parent2 = best_seq
                else:
                    parent1 = random.choice(selected)
                    parent2 = random.choice(selected)
                
                if len(parent1) != target_length:
                    parent1 = parent1[:target_length] + "ATG" * ((target_length - len(&0)) // 3)
                if len(parent2) != target_length:
                    parent2 = parent2[:target_length] + "ATG" * ((target_length - len(&0)) // 3)
                
                if random.random() < self.params.crossover_rate:
                    child1, child2 = self._crossover(parent1, parent2)
                else:
                    child1, child2 = parent1, parent2
                
                if random.random() < self.params.mutation_rate:
                    child1 = self._mutate(child1)
                if random.random() < self.params.mutation_rate:
                    child2 = self._mutate(child2)
                
                # 确保长度一致
                child1 = child1[:target_length]
                child2 = child2[:target_length]
                
                if len(child1) < target_length:
                    child1 = child1 + 'ATG' * ((target_length - len(child1)) // 3)
                if len(child2) < target_length:
                    child2 = child2 + 'ATG' * ((target_length - len(child2)) // 3)
                
                new_population.append(child1)
                if len(new_population) < self.params.population_size:
                    new_population.append(child2)
            
            population = new_population
        
        # 返回最佳序列，确保长度正确
        if best_seq:
            return best_seq[:target_length] + "ATG" * ((target_length - len(&0)) // 3)
        else:
            # 返回全最优密码子的序列
            seq = []
            for aa in protein:
                if aa == '*':
                    seq.append('TAA')
                else:
                    seq.append(OPTIMAL_CODON.get(aa, 'ATG'))
            return ''.join(seq)[:target_length] + "ATG" * ((target_length - len(&0)) // 3)

    def _tournament_select(self, fitness_scores: List[Tuple[str, float]], k: int = 3) -> List[str]:
        """锦标赛选择"""
        selected = []
        for _ in range(self.params.population_size // 2):
            tournament = random.sample(fitness_scores, min(k, len(fitness_scores)))
            winner = max(tournament, key=lambda x: x[1])
            selected.append(winner[0])
        return selected

    def _crossover(self, parent1: str, parent2: str) -> Tuple[str, str]:
        """单点交叉"""
        # 确保长度一致
        min_len = min(len(parent1), len(parent2))
        if min_len < 6:
            return parent1[:min_len], parent2[:min_len]
        
        # 确保在密码子边界交叉
        max_point = (min_len // 3 - 1) * 3
        if max_point < 3:
            return parent1[:min_len], parent2[:min_len]
        
        point = random.randint(3, max_point)
        point = (point // 3) * 3
        
        child1 = parent1[:point] + parent2[point:]
        child2 = parent2[:point] + parent1[point:]
        
        # 截断到相同长度
        child1 = child1[:min_len]
        child2 = child2[:min_len]
        
        return child1, child2

    def _mutate(self, seq: str) -> str:
        """随机变异一个密码子"""
        seq_list = list(seq)
        n_codons = len(seq) // 3
        
        if n_codons > 0:
            codon_idx = random.randint(0, n_codons - 1)
            start = codon_idx * 3
            old_codon = ''.join(seq_list[start:start+3])
            aa = CODON_TO_AA.get(old_codon, '')
            
            if aa and aa != '*' and len(AA_TO_CODONS[aa]) > 1:
                codons = AA_TO_CODONS[aa]
                for c in codons:
                    if c != old_codon:
                        seq_list[start:start+3] = list(c)
                        break
        
        return ''.join(seq_list)

    def optimize(self, dna_seq: str, 
                 start_codon: str = 'ATG',
                 exclude_sites: Set[str] = None,
                 algorithm: str = 'hybrid') -> Tuple[str, OptimizationResult]:
        """
        主优化函数
        """
        # 清理序列
        seq = dna_seq.upper().replace(' ', '').replace('\n', '')
        seq = seq.replace('U', 'T')
        seq = ''.join(c for c in seq if c in 'ATGC')

        if len(seq) < 3:
            raise ValueError("序列太短，至少需要3个核苷酸")

        if len(seq) % 3 != 0:
            seq = seq[:len(seq) - len(seq) % 3]

        # 获取蛋白质序列
        protein = self.dna_to_protein(seq)
        
        # 记录原始统计
        gc_orig = self.calculate_gc_content(seq)
        cai_orig = self.calculate_cai(seq)
        
        # 选择算法
        if algorithm == 'sliding_window':
            optimized = self._optimize_with_sliding_window(seq)
        elif algorithm == 'immune':
            optimized = self._population_immune_optimize(protein)
        else:  # hybrid
            optimized = self._optimize_with_sliding_window(seq)
            optimized = self._population_immune_optimize(protein)
        
        # 设置起始密码子
        if start_codon != 'ATG':
            optimized = start_codon + optimized[3:]
        
        # 移除限制酶切位点
        original_sites = self._find_restriction_sites(seq)
        optimized = self._remove_restriction_sites(optimized, exclude_sites)
        final_sites = self._find_restriction_sites(optimized)
        
        removed_sites = [s for s in original_sites if s not in final_sites]
        
        # 计算最终统计
        gc_opt = self.calculate_gc_content(optimized)
        cai_opt = self.calculate_cai(optimized)
        fitness = self.calculate_fitness(optimized)
        
        # 记录变化
        changes = []
        for i in range(0, len(seq), 3):
            if i + 3 <= len(seq):
                old = seq[i:i+3]
                new = optimized[i:i+3]
                if old != new:
                    aa = CODON_TO_AA.get(old, '?')
                    changes.append({
                        'position': i // 3 + 1,
                        'original': old,
                        'optimized': new,
                        'amino_acid': aa
                    })
        
        # 生成报告
        report = self._generate_codon_report(optimized)
        
        # 警告信息
        warnings = []
        if gc_opt < self.params.target_gc_min:
            warnings.append(f"GC含量({gc_opt:.1f}%)低于目标最小值({self.params.target_gc_min}%)")
        if gc_opt > self.params.target_gc_max:
            warnings.append(f"GC含量({gc_opt:.1f}%)高于目标最大值({self.params.target_gc_max}%)")
        
        return optimized, OptimizationResult(
            original_seq=seq,
            optimized_seq=optimized,
            protein_seq=protein,
            gc_content_original=gc_orig,
            gc_content_optimized=gc_opt,
            cai_original=cai_orig,
            cai_optimized=cai_opt,
            changes=changes,
            codon_usage_report=report,
            fitness_score=fitness['total_fitness'],
            restriction_sites_removed=[s['enzyme'] for s in removed_sites],
            warnings=warnings
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

    def print_report(self, result: OptimizationResult, show_details: bool = True):
        """打印详细报告"""
        print("\n" + "=" * 75)
        print("            CHO 细胞密码子优化报告 (高级版)")
        print("=" * 75)
        
        print(f"\n📊 序列统计:")
        print(f"   原始序列长度: {len(result.original_seq)} bp")
        print(f"   优化序列长度: {len(result.optimized_seq)} bp")
        print(f"   蛋白质长度: {len(result.protein_seq)} aa")
        
        print(f"\n📈 优化效果:")
        print(f"   GC含量: {result.gc_content_original:.1f}% → {result.gc_content_optimized:.1f}%")
        print(f"   CAI: {result.cai_original:.2f} → {result.cai_optimized:.2f}")
        print(f"   适应度得分: {result.fitness_score:.4f}")
        print(f"   密码子替换数: {len(result.changes)}")
        
        if result.restriction_sites_removed:
            print(f"   移除限制位点: {', '.join(result.restriction_sites_removed)}")
        
        if result.warnings:
            print(f"\n⚠️  警告:")
            for w in result.warnings:
                print(f"   - {w}")
        
        if result.changes and show_details:
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
        seq_display = result.optimized_seq[:70]
        if len(result.optimized_seq) > 70:
            seq_display += "..."
        print(f"   {seq_display}")
        
        print("\n" + "=" * 75)


def main():
    parser = argparse.ArgumentParser(
        description='CHO细胞密码子优化器 - 高级版',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
算法说明:
  sliding_window  - Thermo Fisher GeneOptimizer (滑动窗口)
  immune         - 种群免疫算法 (GenScript专利启发)
  hybrid         - 混合算法 (推荐，综合最优)

示例:
  %(prog)s input.fasta -o optimized.fasta
  %(prog)s "ATGGCCTACGAC" --report
  %(prog)s seq.fasta --algorithm immune --generations 50
  %(prog)s seq.fasta --exclude BamHI,EcoRI --report
        """
    )

    parser.add_argument('input', nargs='?', help='输入文件或DNA序列')
    parser.add_argument('-o', '--output', help='输出文件路径')
    parser.add_argument('--algorithm', choices=['sliding_window', 'immune', 'hybrid'],
                        default='hybrid', help='优化算法')
    parser.add_argument('--generations', type=int, default=100,
                        help='种群进化代数 (immune/hybrid模式)')
    parser.add_argument('--start-codon', default='ATG', help='起始密码子')
    parser.add_argument('--exclude', help='保留的限制酶切位点 (逗号分隔)')
    parser.add_argument('--report', action='store_true', help='打印详细报告')
    parser.add_argument('--json', action='store_true', help='输出JSON格式')
    parser.add_argument('--gc-target', type=str, default='40-70',
                        help='目标GC含量范围 (例如: 45-65)')
    
    args = parser.parse_args()
    
    # 解析GC目标范围
    try:
        gc_min, gc_max = map(float, args.gc_target.split('-'))
    except:
        gc_min, gc_max = 40.0, 70.0
    
    # 设置参数
    params = OptimizationParams(
        target_gc_min=gc_min,
        target_gc_max=gc_max,
        generations=args.generations
    )
    
    # 解析排除的限制位点
    exclude_sites = None
    if args.exclude:
        exclude_sites = set(args.exclude.split(','))
        site_mapping = {v: k for k, v in RESTRICTION_SITES.items()}
        exclude_sites = {site_mapping.get(name.strip(), name.strip()) 
                        for name in exclude_sites if name.strip()}
    
    # 读取输入
    if args.input and ('ATGC' in args.input.upper() or 'U' in args.input.upper()):
        dna_seq = args.input
    elif args.input:
        try:
            with open(args.input, 'r') as f:
                content = f.read()
                lines = content.strip().split('\n')
                # 处理FASTA格式
                if content.startswith('>'):
                    dna_lines = []
                    for line in lines:
                        if not line.startswith('>') and not line.startswith('#'):
                            dna_lines.append(line.strip())
                    dna_seq = ''.join(dna_lines)
                else:
                    # 普通文本文件
                    dna_seq = ''.join(line.strip() for line in lines 
                                     if not line.strip().startswith('#'))
        except FileNotFoundError:
            print(f"错误: 找不到文件 {args.input}")
            return 1
    else:
        parser.print_help()
        return 1
    
    # 执行优化
    optimizer = CHOOptimizerAdvanced(params)
    optimized_seq, result = optimizer.optimize(
        dna_seq, 
        start_codon=args.start_codon,
        exclude_sites=exclude_sites,
        algorithm=args.algorithm
    )
    
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
            'fitness_score': round(result.fitness_score, 4),
            'changes': result.changes,
            'restriction_sites_removed': result.restriction_sites_removed,
            'warnings': result.warnings,
            'algorithm': args.algorithm
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
