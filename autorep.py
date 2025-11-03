# -*- coding: utf-8 -*-
"""
Autorep: Auto-generated representation and analysis of tone-bearing units (TBUs)
Designed for computational phonology work.

Features:
- Convert syllabified dictionary forms to Autosegmental representations
- Parses tone strings into association graphs
- Builds labeled matrices (tone–mora, mora–syllable)
- Supports graph drawing, substructure matching, and grammar induction
- Check the superfactors and containment relations  

"""

import os
import re
import graphviz
import numpy as np
import pandas as pd

# Phonology sets
h_tone = set("áéíóú")
l_tone = set("àèìòù")
f_tone = set("âêîôû")
r_tone = set("ǎěǐǒǔ")
untoned = set("aeiou")  # For long vowels (â indicates a short vowel with fall tone; âa a long F)
vowels = h_tone | l_tone | r_tone | f_tone | untoned
tones = h_tone | l_tone  # Combine high and low tones
special_tones = r_tone | f_tone  # Special tones (F, R)


"""
In this program, the tbu will determin how tones are mapped 
1. if syllables, 

"""
WORD_EDGE = True   # HAVENT IMPLEMENTED YET...
MORAIC_CODA = True


class Autorep:

    def __init__(self, word='', ocp_mel='', assoc=None, boundary=0):
        """
        Initialize an Autorep object.
        Parameters:
        - word (str): The word with tone markers.
        - tone (str): The tone markers directly extracted from the word (HFLR).
        - mel (str): The melody (F -> HL and R -> LH) before OCP.
        - ocp_mel (str): The OCP-applied tone representation of the word.
        - assoc (list): A list of tuples (j, k) indicating the association 
                        between tone (indexed by j), mora (indexed by i), 
                        and syllable (indexed by k).
        """
        self.word = word
        self.tone = ""
        self.mel = ""
        self.ocp_mel = ocp_mel
        self.assoc = self.sort_assoc(assoc if assoc is not None else [])
    
        self.boundary = boundary

        self.tone_labels = {"H": h_tone, "L": l_tone, "F": f_tone, "R": r_tone}
        
        
        if self.word:
            self._process_word()
        
        if self.boundary == 1:
            self.ocp_mel_wb = self._wrap()[0]
            self.boundary = self._wrap()[1]
        
        # self.syl_list = [i + 1 for i in range(self.get_max("s"))]
        # self.syl_moralist = [max((tup[1] for tup in self.assoc if tup[-1] == j), default=0) for j in self.syl_list]
  
         
    def _process_word(self):
        """Process the word to extract tones, assign associations, and apply OCP."""
        syllables = self.word.split(".")
        self.tone = "".join(
            next((k for k, v in self.tone_labels.items() if seg in v), "") 
            for seg in self.word
        )
        mora = 0
        if len(syllables) == len(self.tone):
            for i, syl in enumerate(syllables):
                syl_weight = self.check_coda(syl) + self.vowel_count(syl)
                for j in range(syl_weight):
                    self.assoc.extend([(self.tone[i], j+1, i + 1)])
        # print("assoc before flattening:", self.assoc)

       
        self._flatten_tones()  # convert F and R into HL and LH
        self.mel = "".join(tone for tone, _, _ in self.assoc)
        self.ocp_mel = re.sub(r"(.)\1+", r"\1", self.mel)
        self.update_mora_indices(syllables)
     
    def _flatten_tones(self):
        # print(self.assoc)
        tone_map = {"F": ("H", "L"), "R": ("L", "H")}
        for i,tup in enumerate(self.assoc):
            if tup[0] is not None and tup[0] in tone_map:
                t1, t2 = tone_map[tup[0]]
                syl_idx = tup[2]
                weight = max(tup[1] for tup in self.assoc if tup[2] == syl_idx)
                # print(weight)
                if weight > 1:
                    self.assoc[i] = (t1, tup[1], syl_idx)
                    self.assoc[i+1] = (t2, self.assoc[i+1][1], syl_idx)
                if weight == 1:
                    self.assoc[i] = (t1, 1, syl_idx)
                    self.assoc.insert(i+1, (t2, 1, syl_idx))
        
        # print("assoc after flattening:", self.assoc)
                    
        

    def update_mora_indices(self,syllables):
        syl_weight = [self.check_coda(syl) + self.vowel_count(syl) for syl in syllables]
        for i, tup in enumerate(self.assoc): 
            self.assoc[i] = (tup[0], tup[1] + sum(syl_weight[:tup[2]-1]), tup[2])  
        j, i = 0, 0
        while j < len(self.assoc) and i < len(self.ocp_mel):
            if self.assoc[j][0] == self.ocp_mel[i]:
                t, m, s = self.assoc[j]
                self.assoc[j] = (i + 1, m, s)  # Update tone index
                j += 1
            else:
                i += 1
                
    def get_max(self, target):
        """
        self.get_max('t') returns the biggest indexed tone
        self.get_max('s') returns the biggest indexed syllable
        self.get_max('m') returns the total moras
        """
        index_map = {'t': 0, 's': 2}

        if target in index_map:
            return max(
                (item[index_map[target]] for item in self.assoc if item[index_map[target]] is not None), 
                default=0
            )
        elif target == 'm':
            return max([tup[1] for tup in self.assoc if tup[1] is not None], default=0)  # Return the sum of self.moralist if target is 'm'

        return 0  # Return 0 for invalid target
    
    @staticmethod
    def check_coda(syl):
        """Check if a syllable contains a coda."""
        for i in range(1, len(syl)):
            if syl[i] not in vowels and syl[i - 1] in vowels:
                return MORAIC_CODA
        return 0

    @staticmethod
    def vowel_count(syl):
        """Count the number of vowels and adjust for special tones."""
        count = 0
        for i, char in enumerate(syl):
            if char in vowels or char in tones:
                count += 1
            elif (
                char in special_tones
                and i + 1 < len(syl)
                and syl[i + 1] not in vowels
            ):
                count += 2
        return count

    @staticmethod
    def mora_count(string):
        """Count the number of mora in a string."""
        mora_count = 0
        mora_list = []
        syllables = string.split(".")
        for syl in syllables:
            syl_weight = Autorep.check_coda(syl) + Autorep.vowel_count(syl)
            mora_list.append(syl_weight)
            mora_count += syl_weight
        return mora_count, mora_list                                
    
    @staticmethod
    def contour_count(s):
        """Count the number of contour tones in a string."""
        return sum(1 for char in s if char in special_tones)

    @staticmethod
    def index_reset(lst):   

        """Reset indices of the association list to start from 1."""
        if not lst:
            return []
        
        else:
            t_shift = min((t for (t, _, _) in lst if t is not None), default=0)
            
            s_shift = min((s for( _, _, s) in lst if s is not None), default=0)
            # m_shift = min((m for _,m,s in lst if s == s_shift), default= 0)

            return [
                (
                    (t - t_shift + 1) if t else None,
                    m,
                    (s - s_shift + 1) if s else None,
                )
                for (t, m, s) in lst
            ]

    @staticmethod
    def sort_assoc(assoc):
        def custom_compare(x):
            return float('inf') if x is None else x

        sorted_assoc = sorted(
            assoc,
            key=lambda x: (
                custom_compare(x[0]),
                custom_compare(x[2]),
                custom_compare(x[1])
            )
        )
        return sorted_assoc

        
    def check_empty(self):
        """Check if the object is empty."""
        return not (self.word or self.assoc or self.mel or self.ocp_mel)
    
    
    @staticmethod
    def is_modified_substring(list_a, list_b):
        if list_a == list_b:
            return True

        n, m = len(list_a), len(list_b)

        for i in range(m - n + 1):
            window = list_b[i:i+n]
            
            # Skip if list_a[-1] > window[-1]
            if list_a[-1] > window[-1]:
                continue

            # Check middle elements
            middle_match = True
            for a, b in zip(list_a[1:-1], window[1:-1]):
                if a != 0 and a != b:
                    middle_match = False
                    break

            if middle_match:
                return True

        return False


    def add_tone(self):
        """
        Add an unassociated tone in the AR by updating the melody and the association list.
        
        - A new tone ('H' or 'L') is added to the melody.
        - A new association (j, None, None) is added, where:
            - j is one-unit higher than the previous tone's number or 1 if starting fresh.
            - 'None' indicates the syllable is not associated with any tone unit.
        """
        # Copy the existing associations to avoid modifying the original
       
        new_assoc = self.assoc.copy()
        # Determine the next tone to add
        if not self.ocp_mel:  # Empty string case
            return [Autorep(ocp_mel='H', assoc=new_assoc + [(1, None, None)]),
                    Autorep(ocp_mel='L', assoc=new_assoc + [(1, None, None)])]
        
        else:
            # print('adding a tone')
            next_tone = 'H' if self.ocp_mel[-1] == 'L' else 'L'
            next_tone_index = self.get_max('t') + 1
            
            # Create the updated autorep
            return [Autorep(
                ocp_mel=self.ocp_mel + next_tone,
                assoc=new_assoc + [(next_tone_index, None, None)]
            )]
        
    
    
    def add_syl(self):
        new_assoc = self.assoc.copy()
        next_syl_index = self.get_max('s') + 1 if self.get_max('s') else 1
        current_weight = max((tup[1] for tup in self.assoc if tup[2] == self.get_max('s')), default=0)
        new_assoc.append((None, current_weight+1, next_syl_index))
        new_ar = Autorep(ocp_mel= self.ocp_mel,assoc = new_assoc)
        return new_ar

    def add_weight(self, weight):
        new_assoc = self.assoc.copy()
        mora_list = self.syl_mora_list()
        
        if self.get_max('s') > 0:
            current_weight = max((tup[1] for tup in self.assoc if tup[2] == self.get_max('s')), default=0)
            previous_weight = max((tup[1] for tup in self.assoc if tup[2] == self.get_max('s')-1), default=0)
            if current_weight - previous_weight < weight:
                new_assoc.append((None, current_weight+1, self.get_max('s')))

            new_ar = Autorep(ocp_mel=self.ocp_mel, assoc=new_assoc)
            return new_ar


    def add_assoc(self):
        # Gather floating elements and valid connected triples
        floating_tone = min((t for t, m, s in self.assoc if not s), default=None)
        floating_syl = min((s for t, m, s in self.assoc if not t), default=None)
        floating_syl_min_weight = min(
            (m for t, m, s in self.assoc if not t and s == floating_syl), default=None
        )
        valid_connected = [(t, m, s) for t, m, s in self.assoc if t and m and s]

        if floating_tone is None and floating_syl is None:
            return None

        possible_assoc = []

        # Case 1: Floating tone connects to valid syllable
        if floating_tone and valid_connected:
            max_valid_syl = max(s for t, m, s in valid_connected)
            valid_syl_weight = max(m for t, m, s in valid_connected if s == max_valid_syl)

            updated = [
                (t, valid_syl_weight, max_valid_syl) if t == floating_tone else (t, m, s)
                for t, m, s in self.assoc
            ]
            possible_assoc.append(updated)
            # print("float tone to connected syl", updated)

        # Case 2: Floating syllable connects to valid tone
        if floating_syl and valid_connected:
            max_valid_tone = max(t for t, m, s in valid_connected)

            updated = [
                (max_valid_tone, m, s) if s == floating_syl and m == floating_syl_min_weight else (t, m, s)
                for t, m, s in self.assoc
            ]
            possible_assoc.append(updated)
            # print("floating_syl_to_valid_tone", updated)

        # Case 3: Floating tone connects directly to floating syllable
        if floating_tone and floating_syl:
            new_assoc = [
                (floating_tone, m, s)
                if s == floating_syl and m == floating_syl_min_weight else
                (t, m, s)
                for t, m, s in self.assoc
                if not (t == floating_tone and m is None and s is None)  # remove float tone tuple
            ]
            possible_assoc.append(new_assoc)
            # print("float syl to float tone", new_assoc)

        return possible_assoc


    
    def next_ar(self,max_syl_weight):

        next_ar = [self.add_syl()]
        next_ar.extend(self.add_tone())
        
        if self.add_weight(max_syl_weight):
             next_ar.append(self.add_weight(max_syl_weight))
             
        if self.add_assoc():
    # print("adding new assoc")
            for i in self.add_assoc():
                next_ar.append(Autorep('',self.ocp_mel, i))
                
        return next_ar


    def info(self):
        return Autorep(ocp_mel = self.ocp_mel, assoc = self.assoc)

    def show(self):
        print(self.ocp_mel,self.assoc) 

    def fully_spec(self):
        return all(t is not None and m is not None and s is not None for t, m, s in self.assoc)

    def __eq__(self, other):
        if not isinstance(other, Autorep):
            return NotImplemented
        return self.ocp_mel == other.ocp_mel and self.assoc == other.assoc


    def __hash__(self):
        return hash((tuple(self.assoc), self.word))

        
       
    def t_factor(self):
        tone_num = len(self.ocp_mel)
        return tone_num
    
    def s_factor(self):
        syl_num = max([k for _,_,k in self.assoc if k is not None], default=0)
        return syl_num     

    def k_factor(self):
        return self.t_factor() + self.s_factor()
    
    def __repr__(self):
        return f"{self.ocp_mel}, {self.assoc}"
    
        
    def draw(self, suffix='svg', output_dir = 'output'):
        """
        Draws a Graphviz diagram and save it as an image

        Args:
            output (bool): If True, saves the graph to file. If False, displays inline.
            suffix (str): File format to export (e.g., 'svg', 'png', 'pdf').

        Returns:
            file path
        """
        
        drawing = self.assoc[:]

        for i, tup in enumerate(self.assoc, start=1):
            if tup[1] is not None or tup[2] is not None:
                drawing[i - 1] = (tup[0], i, tup[2])

        
    
        os.makedirs(output_dir, exist_ok=True)

        

        file_name = self.ocp_mel + '_' + '_'.join(
                ''.join(str(x or 0) for x in tup) for tup in self.assoc
            )


        file_path = os.path.join(output_dir, file_name)


        # Initialize Graphviz
        d = graphviz.Digraph(filename=file_path, format=suffix)

        # Global layout tuning
        d.attr(nodesep="0.01", ranksep="0.05", margin="0", fontsize="10")

        # Melody nodes
        with d.subgraph() as s1:
            s1.attr(rank='source', rankdir='LR')
            for i, t in enumerate(self.ocp_mel):
                s1.node(f'Mel_{i+1}', label=t, shape='plaintext', fontsize="10", width="0", height="0")

        # Track added edges to avoid duplicates
        seen_edges = set()

        # Add σ and mora nodes, mora→σ edges
        for t, m, s in self.assoc:
            if m:
                d.node(f'Syl_{s}', label='σ', shape='plaintext', fontsize="10", width="0", height="0")
                d.node(f'Mora_{m}', label="μ", shape='plaintext', fontsize="10", width="0", height="0")
                mora_to_syl_edge = (f'Mora_{m}', f'Syl_{s}')
                if mora_to_syl_edge not in seen_edges:
                    d.edge(*mora_to_syl_edge, dir='none', arrowsize="0.5", penwidth="0.5")
                    seen_edges.add(mora_to_syl_edge)

        # Add mel→mora edges
        # for t, m, s in self.assoc:
            if t and m:
                mel_to_mora_edge = (f'Mel_{t}', f'Mora_{m}')
                if mel_to_mora_edge not in seen_edges:
                    d.edge(*mel_to_mora_edge, dir='none', arrowsize="0.5", penwidth="0.5")
                    seen_edges.add(mel_to_mora_edge)

        d.render(cleanup=True)
        return file_path + "." + suffix


    def tone_syl_list(self):
            tone_syl_list = []
            prev_max = 0  # Store max(tup[2]) of previous tone index
            
            if self.ocp_mel:
                for i in range(self.get_max('t')):  # Loop through tone indices
                    # Extract `tup[2]` values where `tup[0] == i+1` and `tup[2] is not None`
                    syl_values = [tup[2] for tup in self.assoc if tup[0] == i + 1 and tup[2] is not None]
                    
                    # Compute max(tup[2]) for current tone index
                    current_max = max(syl_values) if syl_values else prev_max  
                    
                    # Compute span: difference from previous max
                    i_tone_syl = current_max - prev_max if current_max!= prev_max else 1
                    tone_syl_list.append(i_tone_syl)
                    
                    # Update prev_max for next iteration
                    prev_max = current_max  
            
            return tone_syl_list
            
    def syl_tone_list(self):
        syl_tone_list = []
        max_s = self.get_max('s')
        
        for s in range(1, max_s + 1):  # 1-indexed syllables
            tone_count = set(tup[0] for tup in self.assoc if tup[2] == s and tup[0] is not None)
            syl_tone_list.append(len(tone_count))
            # print(f"→ Syllable {s} has {tone_count} tone(s)")
        
        # print(f"✅ syl_tone_list: {syl_tone_list}")
        return syl_tone_list

    
    def syl_mora_list(self):
        syl_mora_list = []
        if self.get_max('s') > 0:
            for i in range(self.get_max('s')):
                mora_values = len(set([tup[1] for tup in self.assoc if tup[2] == i+1 and tup[1] is not None]))
                syl_mora_list.append(mora_values)
        return syl_mora_list


    def mora_tone_list(self):
        max_s = self.get_max('s')
        mora_tone_list = []

        for s in range(1, max_s + 1):  # Syllables assumed to be 1-indexed
            # Get the maximum mora index for syllable `s` (0 if all are None)
            moras = max(
                [tup[1] if tup[1] is not None else 0 for tup in self.assoc if tup[-1] == s],
                default=0
            )
            # print(f'Syllable {s} has {moras} mora(s)')

            for mora in range(1, moras + 1):  # Moras also assumed to be 1-indexed
                tone_count = 0
                for tup in self.assoc:
                    tone, mora_idx, syllable_idx = tup
                    if syllable_idx == s and mora_idx == mora and tone is not None:
                        tone_count += 1

                # print(f'  → Mora {mora} in syllable {s} has {tone_count} tone(s)')
                mora_tone_list.append(tone_count)

        # print(f'Final mora_tone_list: {mora_tone_list}')
        return mora_tone_list


    
    def tone_mora_list(self):
        result = []
        max_t = self.get_max('t')
        for t in range(1, max_t + 1):  # Assuming syllable indexing starts from 1
            mora = set()
            moras = set(tup for tup in self.assoc if tup[0] == t and tup[1] is not None)
            result.append(len(moras))
        return result

    def build_labeled_matrices(self):
        max_t = self.get_max('t')
        max_m = self.get_max('m')
        max_s = self.get_max('s')

        # Create zero matrices
        M_tm = np.zeros((max_m, max_t), dtype=int)
        M_ms = np.zeros((max_s, max_m), dtype=int)

                # Fill in the matrices
        for (t, m, s) in self.assoc:
            if t is not None and m is not None:
                M_tm[m-1, t-1] = 1
            if m is not None and s is not None:
                M_ms[s-1, m-1] = 1

        # Create labeled DataFrames
        M_tm_df = pd.DataFrame(M_tm,
                            index=[f"m{m+1}" for m in range(max_m)],
                            columns=[t for t in self.ocp_mel])
        
        M_ms_df = pd.DataFrame(M_ms,
                            index=[f"s{s+1}" for s in range(max_s)],
                            columns=[f"m{m+1}" for m in range(max_m)])

        return M_tm_df, M_ms_df

   
    
    def check_adj_contain(container, containee):
        if containee.check_empty():
            # print("containee is empty")
            return True
        if container.check_empty():
            # print("container is empty")
            return False
        
        if not containee.mora_tone_list():
            return containee.ocp_mel in container.ocp_mel  # If no syllables, check melody
        
        if not containee.ocp_mel:
            return containee.is_modified_substring(containee.syl_mora_list(),container.syl_mora_list())

        match_positions = [m.start() for m in re.finditer(f"(?={re.escape(containee.ocp_mel)})", container.ocp_mel)]
        # print("match positions", match_positions)
        if not match_positions:
            # print("no match positions")
            return False

        containee_tm, containee_ms = containee.build_labeled_matrices()
        container_tm, container_ms = container.build_labeled_matrices()

        if (containee_tm.shape[0] > container_tm.shape[0] or
            containee_ms.shape[1] > container_ms.shape[1]):
            return False

        for match_tone in match_positions:
            
            first_l_assoc_index = container_tm[container_tm.iloc[:, match_tone] == 1].index
            if not first_l_assoc_index.empty:
                first_l_assoc_index =first_l_assoc_index[0]
                # print("first_l_assoc_index", first_l_assoc_index)
                res_tm = container_tm.loc[first_l_assoc_index:,]
                res_tm = res_tm.iloc[:, match_tone:match_tone + containee_tm.shape[1]]
                res_ms = container_ms.loc[:,first_l_assoc_index:]
                # print("res_tm", res_tm)
                # print("res_ms", res_ms)
                for i in range(res_tm.shape[0] - containee_tm.shape[0] + 1):
                    tm_slice = res_tm.iloc[i:i + containee_tm.shape[0], :]
                    
                    # print("\nchecking tm match \n")
                    # print(tm_slice)
                    # print("vs")
                    # print(containee_tm)
                    

                    if np.all(tm_slice.values >= containee_tm.values):
                        for j in range(res_ms.shape[0] - containee_ms.shape[0] + 1):
                            ms_slice = res_ms.iloc[j:j+containee_ms.shape[0],i:i+containee_ms.shape[1]]
                            # print(f'ms_slice\n {ms_slice}')
                            # print("vs")
                            # print(containee_ms)
                            # print("\nchecking ms match \n")
                            if np.all(ms_slice.values >= containee_ms.values):
                                return True
        return False