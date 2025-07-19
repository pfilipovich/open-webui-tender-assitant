import { WEBUI_API_BASE_URL } from '$lib/constants';

export interface ChecklistItem {
    id: string;
    checklist_id: string;
    prompt_command: string;
    order_index: number;
    settings?: Record<string, any>;
}

export interface Checklist {
    id: string;
    command: string;
    user_id: string;
    title: string;
    description?: string;
    timestamp: number;
    access_control?: Record<string, any>;
    items: ChecklistItem[];
}

export interface ChecklistForm {
    command: string;
    title: string;
    description?: string;
    access_control?: Record<string, any>;
    items: {
        prompt_command: string;
        order_index: number;
        settings?: Record<string, any>;
    }[];
}

export interface ChecklistUserResponse extends Checklist {
    user?: {
        id: string;
        name: string;
        email: string;
    };
}

export const createNewChecklist = async (token: string, checklist: ChecklistForm): Promise<Checklist> => {
    let error = null;

    const res = await fetch(`${WEBUI_API_BASE_URL}/checklists/create`, {
        method: 'POST',
        headers: {
            Accept: 'application/json',
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(checklist)
    });

    if (!res.ok) {
        error = await res.json();
        throw error;
    }

    return await res.json();
};

export const getChecklists = async (token: string): Promise<ChecklistUserResponse[]> => {
    let error = null;

    const res = await fetch(`${WEBUI_API_BASE_URL}/checklists/`, {
        method: 'GET',
        headers: {
            Accept: 'application/json',
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
        }
    });

    if (!res.ok) {
        error = await res.json();
        throw error;
    }

    return await res.json();
};

export const getChecklistList = async (token: string): Promise<ChecklistUserResponse[]> => {
    let error = null;

    const res = await fetch(`${WEBUI_API_BASE_URL}/checklists/list`, {
        method: 'GET',
        headers: {
            Accept: 'application/json',
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
        }
    });

    if (!res.ok) {
        error = await res.json();
        throw error;
    }

    return await res.json();
};

export const getChecklistByCommand = async (token: string, command: string): Promise<Checklist> => {
    let error = null;

    const res = await fetch(`${WEBUI_API_BASE_URL}/checklists/command/${command}`, {
        method: 'GET',
        headers: {
            Accept: 'application/json',
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
        }
    });

    if (!res.ok) {
        error = await res.json();
        throw error;
    }

    return await res.json();
};

export const updateChecklistByCommand = async (
    token: string,
    command: string,
    checklist: ChecklistForm
): Promise<Checklist> => {
    let error = null;

    const res = await fetch(`${WEBUI_API_BASE_URL}/checklists/command/${command}/update`, {
        method: 'POST',
        headers: {
            Accept: 'application/json',
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(checklist)
    });

    if (!res.ok) {
        error = await res.json();
        throw error;
    }

    return await res.json();
};

export const deleteChecklistByCommand = async (token: string, command: string): Promise<boolean> => {
    let error = null;

    const res = await fetch(`${WEBUI_API_BASE_URL}/checklists/command/${command}/delete`, {
        method: 'DELETE',
        headers: {
            Accept: 'application/json',
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
        }
    });

    if (!res.ok) {
        error = await res.json();
        throw error;
    }

    return await res.json();
};