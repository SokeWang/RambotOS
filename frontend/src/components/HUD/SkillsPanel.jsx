import React, { useState, useEffect, useCallback } from 'react';
import { Activity, Plus, Trash2, Edit, Search } from 'lucide-react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Modal from '../ui/Modal';

export default function SkillsPanel() {
    const [skills, setSkills] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [showModal, setShowModal] = useState(false);
    const [currentSkill, setCurrentSkill] = useState(null);
    const [formData, setFormData] = useState({ name: '', description: '' });

    const fetchSkills = useCallback(async () => {
        setLoading(true);
        try {
            const response = await fetch('http://127.0.0.1:8000/skills');
            if (response.ok) {
                const data = await response.json();
                setSkills(data);
            }
        } catch (e) {
            console.error("Failed to fetch skills:", e);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchSkills();
    }, [fetchSkills]);

    const handleCreateUpdate = async () => {
        try {
            if (currentSkill) {
                const response = await fetch(`http://127.0.0.1:8000/skills/${currentSkill.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: formData.name, description: formData.description })
                });
                if (response.ok) {
                    fetchSkills();
                    setShowModal(false);
                }
            } else {
                const response = await fetch('http://127.0.0.1:8000/skills', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: formData.name, description: formData.description })
                });
                if (response.ok) {
                    fetchSkills();
                    setShowModal(false);
                }
            }
        } catch (error) {
            console.error("Failed to save skill:", error);
        }
    };

    const handleDelete = async (skillId) => {
        if (window.confirm(`Are you sure you want to delete ${skillId}?`)) {
            try {
                const response = await fetch(`http://127.0.0.1:8000/skills/${skillId}`, {
                    method: 'DELETE'
                });
                if (response.ok) {
                    fetchSkills();
                }
            } catch (error) {
                console.error("Failed to delete skill:", error);
            }
        }
    };

    const openModal = (skill = null) => {
        setCurrentSkill(skill);
        setFormData(skill ? { name: skill.name, description: skill.description } : { name: '', description: '' });
        setShowModal(true);
    };

    const filteredSkills = skills.filter(s =>
        (s.name || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
        (s.description || '').toLowerCase().includes(searchQuery.toLowerCase())
    );

    return (
        <div className="p-12 overflow-y-auto w-full h-full custom-scrollbar">
            <div className="flex justify-between items-center mb-10">
                <div>
                    <h1 className="text-4xl font-black text-white tracking-tight mb-2">Skill Matrix</h1>
                    <p className="text-white/40 uppercase tracking-widest text-xs font-bold">Manage system capabilities</p>
                </div>
                <Button onClick={() => openModal()} className="flex items-center gap-2">
                    <Plus size={18} /> Add New Skill
                </Button>
            </div>

            <div className="relative mb-10">
                <Search className="absolute left-6 top-1/2 -translate-y-1/2 text-white/30" size={20} />
                <Input
                    placeholder="Search skills..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-16 w-full"
                />
            </div>

            {loading ? (
                <div className="flex items-center justify-center p-20">
                    <div className="w-10 h-10 border-4 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin" />
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 pb-10">
                    {filteredSkills.map(skill => (
                        <Card key={skill.id} className="group relative overflow-hidden flex flex-col h-full">
                            <div className="flex justify-between items-start mb-4">
                                <div className="p-3 rounded-2xl bg-cyan-500/10 text-cyan-400 group-hover:scale-110 transition-transform">
                                    <Activity size={24} />
                                </div>
                                <div className="flex gap-2">
                                    <button
                                        onClick={(e) => { e.stopPropagation(); openModal(skill); }}
                                        className="p-2 hover:bg-white/10 rounded-xl text-white/40 hover:text-white transition-colors"
                                    >
                                        <Edit size={16} />
                                    </button>
                                    <button
                                        onClick={(e) => { e.stopPropagation(); handleDelete(skill.id); }}
                                        className="p-2 hover:bg-red-500/20 rounded-xl text-white/40 hover:text-red-400 transition-colors"
                                    >
                                        <Trash2 size={16} />
                                    </button>
                                </div>
                            </div>
                            <h3 className="text-xl font-bold text-white mb-2">{skill.name}</h3>
                            <p className="text-sm text-white/50 line-clamp-3 flex-grow">{skill.description || 'No description provided.'}</p>
                            <div className="mt-6 pt-4 border-t border-white/5 flex items-center justify-between">
                                <span className="text-[10px] font-bold text-white/20 uppercase tracking-widest">{skill.id}</span>
                            </div>
                        </Card>
                    ))}
                    {filteredSkills.length === 0 && !loading && (
                        <div className="col-span-full py-20 text-center">
                            <div className="inline-flex p-6 rounded-full bg-white/5 text-white/20 mb-6">
                                <Activity size={48} />
                            </div>
                            <p className="text-white/40">No skills found matching your search.</p>
                        </div>
                    )}
                </div>
            )}

            <Modal
                isOpen={showModal}
                onClose={() => setShowModal(false)}
                title={currentSkill ? "Edit Skill" : "Create New Skill"}
            >
                <div className="space-y-6">
                    <div>
                        <label className="block text-xs font-bold text-white/40 uppercase tracking-widest mb-2">Skill Name</label>
                        <Input
                            value={formData.name}
                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                            placeholder="e.g., Stock Market"
                            className="w-full"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-bold text-white/40 uppercase tracking-widest mb-2">Description</label>
                        <textarea
                            value={formData.description}
                            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                            placeholder="What does this skill do?"
                            className="w-full bg-white/5 border border-white/10 rounded-[1.5rem] p-4 text-white focus:outline-none focus:border-cyan-500/50 transition-colors h-32 resize-none"
                        />
                    </div>
                    <div className="flex justify-end gap-4 mt-8">
                        <Button variant="ghost" onClick={() => setShowModal(false)}>Cancel</Button>
                        <Button onClick={handleCreateUpdate}>
                            {currentSkill ? "Save Changes" : "Initialize Skill"}
                        </Button>
                    </div>
                </div>
            </Modal>
        </div>
    );
}
