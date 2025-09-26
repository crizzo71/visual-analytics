#!/usr/bin/env python3
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

# Data from the seniority analysis
levels = ['Principal\nLevel', 'Senior\nLevel', 'Mid-Level', 'Leadership', 'Junior\nLevel']
counts = [7, 4, 4, 1, 1]
percentages = [41.2, 23.5, 23.5, 5.9, 5.9]

# Create figure with two subplots
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

# Colors for each level
colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#8B5A3C']

# Bar chart
bars = ax1.bar(levels, counts, color=colors, alpha=0.8, edgecolor='black', linewidth=1)
ax1.set_title('Team Seniority Distribution\n(Christine Rizzo\'s Team - 17 Total)', fontsize=14, fontweight='bold')
ax1.set_ylabel('Number of Team Members', fontsize=12)
ax1.set_xlabel('Seniority Level', fontsize=12)

# Add value labels on bars
for bar, count in zip(bars, counts):
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height + 0.1,
             f'{count}', ha='center', va='bottom', fontweight='bold')

ax1.grid(axis='y', alpha=0.3)
ax1.set_ylim(0, max(counts) + 1)

# Pie chart
wedges, texts, autotexts = ax2.pie(counts, labels=levels, colors=colors, autopct='%1.1f%%',
                                   startangle=90, textprops={'fontsize': 10})
ax2.set_title('Seniority Distribution\n(Percentage Breakdown)', fontsize=14, fontweight='bold')

# Improve pie chart text
for autotext in autotexts:
    autotext.set_color('white')
    autotext.set_fontweight('bold')

plt.tight_layout()
plt.savefig('team_seniority_chart.png', dpi=300, bbox_inches='tight')
print('✅ Chart saved as team_seniority_chart.png')

# Also create a text-based chart
print('\n📊 TEAM SENIORITY DISTRIBUTION')
print('=' * 50)
print(f'{"Level":<15} {"Count":<8} {"Percentage":<12} {"Visual":<20}')
print('-' * 50)

for level, count, pct in zip(['Principal', 'Senior', 'Mid-Level', 'Leadership', 'Junior'], counts, percentages):
    bar = '█' * int(pct/2.5)  # Scale for display
    print(f'{level:<15} {count:<8} {pct:>6.1f}%     {bar}')

print('-' * 50)
print(f'{"TOTAL":<15} {sum(counts):<8} {"100.0%":<12}')