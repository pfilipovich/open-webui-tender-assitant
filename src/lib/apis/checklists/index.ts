import { WEBUI_API_BASE_URL } from '$lib/constants';

type ChecklistItem = {
    title: string;
    items: { question: string }[];
    access_control?: null | object;
};

export const createNewChecklist = async (token: string, checklist: ChecklistItem) => {
    let error = null;

    const res = await fetch(`${WEBUI_API_BASE_URL}/checklists/create`, {
        method: 'POST',
        headers: {
            Accept: 'application/json',
            'Content-Type': 'application/json',
            authorization: `Bearer ${token}`
        },
        body: JSON.stringify(checklist)
    })
        .then(async (res) => {
            if (!res.ok) throw await res.json();
            return res.json();
        })
        .catch((err) => {
            error = err.detail;
            console.error(err);
            return null;
        });

    if (error) {
        throw error;
    }

    return res;
};

export const getChecklists = async (token: string = '') => {
    let error = null;

    const res = await fetch(`${WEBUI_API_BASE_URL}/checklists/`, {
        method: 'GET',
        headers: {
            Accept: 'application/json',
            'Content-Type': 'application/json',
            authorization: `Bearer ${token}`
        }
    })
        .then(async (res) => {
            if (!res.ok) throw await res.json();
            return res.json();
        })
        .then((json) => json)
        .catch((err) => {
            error = err.detail;
            console.error(err);
            return null;
        });

    if (error) {
        throw error;
    }

    return res;
};

export const getChecklistList = async (token: string = '') => {
    let error = null;

    const res = await fetch(`${WEBUI_API_BASE_URL}/checklists/list`, {
        method: 'GET',
        headers: {
            Accept: 'application/json',
            'Content-Type': 'application/json',
            authorization: `Bearer ${token}`
        }
    })
        .then(async (res) => {
            if (!res.ok) throw await res.json();
            return res.json();
        })
        .then((json) => json)
        .catch((err) => {
            error = err.detail;
            console.error(err);
            return null;
        });

    if (error) {
        throw error;
    }

    return res;
};

export const getChecklistById = async (token: string, id: string) => {
    let error = null;

    const res = await fetch(`${WEBUI_API_BASE_URL}/checklists/${id}`, {
        method: 'GET',
        headers: {
            Accept: 'application/json',
            'Content-Type': 'application/json',
            authorization: `Bearer ${token}`
        }
    })
        .then(async (res) => {
            if (!res.ok) throw await res.json();
            return res.json();
        })
        .then((json) => json)
        .catch((err) => {
            error = err.detail;
            console.error(err);
            return null;
        });

    if (error) {
        throw error;
    }

    return res;
};

export const updateChecklistById = async (token: string, id: string, checklist: ChecklistItem) => {
    let error = null;

    const res = await fetch(`${WEBUI_API_BASE_URL}/checklists/${id}/update`, {
        method: 'POST',
        headers: {
            Accept: 'application/json',
            'Content-Type': 'application/json',
            authorization: `Bearer ${token}`
        },
        body: JSON.stringify(checklist)
    })
        .then(async (res) => {
            if (!res.ok) throw await res.json();
            return res.json();
        })
        .then((json) => json)
        .catch((err) => {
            error = err.detail;
            console.error(err);
            return null;
        });

    if (error) {
        throw error;
    }

    return res;
};

export const deleteChecklistById = async (token: string, id: string) => {
    let error = null;

    const res = await fetch(`${WEBUI_API_BASE_URL}/checklists/${id}/delete`, {
        method: 'DELETE',
        headers: {
            Accept: 'application/json',
            'Content-Type': 'application/json',
            authorization: `Bearer ${token}`
        }
    })
        .then(async (res) => {
            if (!res.ok) throw await res.json();
            return res.json();
        })
        .then((json) => json)
        .catch((err) => {
            error = err.detail;
            console.error(err);
            return null;
        });

    if (error) {
        throw error;
    }

    return res;
};
